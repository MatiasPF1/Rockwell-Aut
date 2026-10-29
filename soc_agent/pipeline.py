"""The L1 investigation pipeline.

alert -> data-quality checks -> similar historical incidents -> playbook(s) from
those incidents' alert types -> model works the playbook steps -> post checks ->
confidence -> human-in-the-loop gates -> report. Every stage is a trace span.
"""

import uuid
from collections import defaultdict
from datetime import datetime, timezone

from . import config, hitl, quality, report, store
from .confidence import score as score_confidence
from .data import get_alert, load_incidents
from .llm import LLM, InvestigationRequest, LLMError, get_llm
from .models import Decision, IncidentMatch, Playbook
from .playbooks import load_playbooks, playbooks_by_type, rules_for
from .retrieval import get_retriever
from .trace import Tracer, find_span, now_ms


def select_playbooks(matches: list[IncidentMatch]) -> tuple[list[Playbook], dict[str, float]]:
    """Primary playbook from the best-scoring incident type, plus a close runner-up.

    Returns no playbook when nothing matched well; the alert is then handled as novel.
    """
    by_type: dict[str, float] = defaultdict(float)
    for m in matches:
        if m.score >= config.NOVELTY_THRESHOLD:  # too-weak matches don't pick a playbook
            by_type[m.incident.alert_type] += m.score
    books = playbooks_by_type()
    ranked = sorted(((t, s) for t, s in by_type.items() if t in books), key=lambda x: x[1], reverse=True)
    if not ranked:
        return [], dict(by_type)
    selected = [books[ranked[0][0]]]
    if len(ranked) > 1 and ranked[1][1] >= config.SECONDARY_PLAYBOOK_RATIO * ranked[0][1]:
        selected.append(books[ranked[1][0]])
    return selected, dict(by_type)


def new_run(alert_id: str) -> dict:
    alert = get_alert(alert_id)
    run = {
        "run_id": f"{datetime.now(timezone.utc):%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:6]}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "running",
        "alert": alert.model_dump(),
        "llm_backend": config.LLM_BACKEND,
        "trace": [],
        "gates": [],
    }
    store.save(run)
    return run


def investigate(run: dict, llm: LLM | None = None) -> dict:
    llm = llm or get_llm()
    tracer = Tracer(on_change=lambda: store.save(run))
    tracer.spans = run["trace"]
    alert = get_alert(run["alert"]["alert_id"])

    try:
        with tracer.span(f"investigate {alert.alert_id}", "root", alert_id=alert.alert_id) as root:
            with tracer.span("load_alert", "io", origin=alert.origin) as s:
                s["output"] = alert.model_dump()

            with tracer.span("data_quality.pre", "check") as s:
                flags = quality.check_alert(alert)
                s["output"] = [f.model_dump() for f in flags]

            retriever = get_retriever()
            with tracer.span("retrieve_historical_incidents", "retrieval", retriever=retriever.name, k=config.RETRIEVAL_TOP_K) as s:
                s["input"] = {"description": alert.description}
                matches = retriever.retrieve(alert, load_incidents(), config.RETRIEVAL_TOP_K)
                run["matches"] = [m.model_dump() for m in matches]
                s["output"] = [{"incident_id": m.incident.incident_id, "alert_type": m.incident.alert_type, "score": m.score} for m in matches]

            with tracer.span("select_playbooks", "playbook") as s:
                selected, type_scores = select_playbooks(matches)
                rules = [r for b in selected for r in rules_for(b.slug)]
                run["playbooks"] = [{"slug": b.slug, "path": b.path, "alert_type": b.alert_type, "origin": b.origin} for b in selected]
                s["input"] = {"type_scores": type_scores}
                s["output"] = {"selected": [b.slug for b in selected], "human_rules": [r.model_dump() for r in rules]}

            knowledge_base = load_playbooks()
            req = InvestigationRequest(alert=alert, flags=flags, matches=matches, selected=selected, rules=rules, knowledge_base=knowledge_base)
            with tracer.span("llm.investigate", "llm", backend=llm.name, model=getattr(llm, "model", llm.name)) as s:
                s["input"] = {"selected_playbooks": [b.slug for b in selected], "flags": len(flags), "incidents": len(matches)}
                result = llm.investigate(req)
                inv = result.investigation
                s["attributes"].update(model=result.model, usage=result.usage, request_id=result.request_id)
                s["output"] = {
                    "incident_type": inv.incident_type,
                    "assessed_severity": inv.assessed_severity,
                    "recommended_action": inv.recommended_action,
                    "classification_rationale": inv.classification_rationale,
                    "reasoning_summary": result.reasoning_summary,
                }
                for step in inv.steps:
                    tracer.event(f"{step.phase}: {step.playbook_quote[:70]}", "step", output=step.model_dump(),
                                 owner=step.owner, status=step.status, playbook=step.playbook)
            run["investigation"] = inv.model_dump()

            with tracer.span("data_quality.post", "check") as s:
                post = quality.check_against_investigation(alert, matches, inv)
                flags = flags + post
                run["quality_flags"] = [f.model_dump() for f in flags]
                s["output"] = [f.model_dump() for f in post]

            with tracer.span("confidence", "score") as s:
                conf = score_confidence(matches, len(selected) > 1, flags, inv)
                run["confidence"] = conf.model_dump()
                s["output"] = run["confidence"]

            with tracer.span("hitl.policy", "policy") as s:
                gates, violations = hitl.evaluate(alert, inv, conf, selected, rules, knowledge_base)
                run["policy_violations"] = violations
                s["output"] = {"gates": [g.title for g in gates], "violations": violations}

            for gate in gates:
                span = tracer.start(f"human: {gate.title}", "human", parent_id=root["span_id"], gate_id=gate.gate_id, blocking=gate.blocking)
                span["status"] = "waiting"
                gate.payload["span_id"] = span["span_id"]
            run["gates"] = [g.model_dump() for g in gates]
            run["final_action"] = hitl.final_action(run)
            run["status"] = hitl.run_status(run)
            tracer.event("report", "report", status=run["status"])
    except LLMError as e:
        run["error"] = str(e)
    except Exception as e:  # keep the trace; surface the failure in the UI
        run["error"] = f"{type(e).__name__}: {e}"

    if run.get("error"):
        run["status"] = "failed"
        run.setdefault("final_action", {"action": "escalate", "by": "policy", "note": "Agent failed; route to an analyst"})
    run["report"] = report.build(run)
    store.save(run)
    return run


def run_alert(alert_id: str, llm: LLM | None = None) -> dict:
    return investigate(new_run(alert_id), llm)


def decide(run_id: str, gate_id: str, decision: Decision) -> dict:
    run = store.load(run_id)
    gate = hitl.apply_decision(run, gate_id, decision)
    span = find_span(run["trace"], gate.payload["span_id"])
    span["end"] = now_ms()
    span["status"] = gate.status
    span["output"] = gate.decision
    run["report"] = report.build(run)
    store.save(run)
    return run
