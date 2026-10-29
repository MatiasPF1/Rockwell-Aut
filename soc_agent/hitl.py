"""Human-in-the-loop policy: which results need a person, and applying their decisions.

Gates:
- action_approval: the recommended action needs sign-off (by action x severity,
  low confidence, or a large severity downgrade).
- act_then_confirm: the playbook says act immediately (ransomware, malware); the
  action stands but a person must confirm it afterwards.
- playbook_step: a step the playbook overlay marks as human-owned.
- playbook_proposal: the agent drafted a new playbook or addendum. Approved drafts
  go to playbook_proposals/approved/; Playbooks/ is never modified.
"""

import difflib
import re
import uuid
from datetime import datetime, timezone

from . import config
from .confidence import Confidence
from .models import SEVERITY_ORDER, Alert, Decision, Gate, Investigation, Playbook, StepRule
from .playbooks import L1_PHASES, normalize

CONTACT_USER_RE = re.compile(r"\b(contact|notify|email|call|message|ask)\b[^.]*\b(the )?(user|employee)\b", re.I)


def _gate(kind: str, title: str, reason: str, blocking: bool, **payload) -> Gate:
    return Gate(gate_id=uuid.uuid4().hex[:8], kind=kind, title=title, reason=reason, blocking=blocking, payload=payload)


def _phase_of(rule: StepRule, book: Playbook) -> str | None:
    for phase, text in book.sections.items():
        if normalize(rule.match) in text:
            return phase
    return None


def evaluate(
    alert: Alert,
    inv: Investigation,
    conf: Confidence,
    selected: list[Playbook],
    rules: list[StepRule],
    knowledge_base: dict[str, Playbook],
) -> tuple[list[Gate], list[str]]:
    """Return the gates this run needs and any policy violations found."""
    gates: list[Gate] = []
    violations: list[str] = []
    action, sev = inv.recommended_action, inv.assessed_severity
    high = sev in ("High", "Critical")
    fast_path = next((r for r in rules if r.gate == "act_then_confirm"), None)

    reasons = []
    if conf.score < config.LOW_CONFIDENCE_THRESHOLD:
        reasons.append(f"confidence {conf.score} is below {config.LOW_CONFIDENCE_THRESHOLD}")
    if alert.severity in SEVERITY_ORDER and SEVERITY_ORDER.index(alert.severity) - SEVERITY_ORDER.index(sev) >= 2:
        reasons.append(f"severity downgraded {alert.severity} -> {sev}")
    if action == "isolate" and not fast_path:
        reasons.append("isolation changes production systems")
    if action == "escalate":
        reasons.append("escalation hands the case to Level 2")
    if action == "close" and (high or conf.score < config.AUTO_CLOSE_CONFIDENCE):
        reasons.append("closing needs high confidence on a Low/Medium alert to run unattended")

    if action == "isolate" and fast_path and not reasons:
        gates.append(_gate(
            "act_then_confirm", "Confirm isolation", f'Playbook `{fast_path.playbook}` says: "{fast_path.match}"',
            blocking=False, action=action, severity=sev,
        ))
    elif reasons:
        gates.append(_gate(
            "action_approval", f"Approve action: {action}", "; ".join(reasons),
            blocking=True, action=action, severity=sev,
        ))

    for rule in rules:
        book = knowledge_base.get(rule.playbook)
        if rule.owner == "human" and rule.gate == "blocking" and book and _phase_of(rule, book) in L1_PHASES:
            gates.append(_gate(
                "playbook_step", "Human step required", rule.note or "Playbook step owned by a person",
                blocking=True, playbook=rule.playbook, quote=rule.match,
            ))

    if any(r.constraint == "no_user_contact" for r in rules):
        for text in [*inv.next_actions, *(s.finding for s in inv.steps)]:
            if CONTACT_USER_RE.search(text):
                violations.append(f"Recommends contacting the user despite the no-user-contact constraint: {text!r}")

    if inv.playbook_proposal:
        p = inv.playbook_proposal
        base = knowledge_base[p.target_playbook].text if p.kind == "addendum" and p.target_playbook in knowledge_base else ""
        proposed = base + ("\n\n" if base else "") + p.markdown
        gates.append(_gate(
            "playbook_proposal", f"Playbook {p.kind.replace('_', ' ')}: {p.title}", p.rationale,
            blocking=False, proposal=p.model_dump(), diff=unified_diff(base, proposed, p.target_playbook or "new"),
        ))
    return gates, violations


def unified_diff(before: str, after: str, name: str) -> str:
    return "".join(difflib.unified_diff(
        before.splitlines(keepends=True), after.splitlines(keepends=True),
        fromfile=f"a/{name}.md", tofile=f"b/{name}.md",
    ))


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:60] or "proposal"


def write_approved_proposal(run_id: str, gate: Gate, decision: Decision) -> str:
    p = gate.payload["proposal"]
    body = decision.edited_markdown if decision.decision == "modify" and decision.edited_markdown else p["markdown"]
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = slugify(p["target_playbook"] + "_addendum" if p["kind"] == "addendum" and p["target_playbook"] else p["title"])
    header = (
        f"<!-- AI-drafted in run {run_id}; {decision.decision}d by {decision.reviewer} on {stamp}. "
        f"Not an official playbook. Kind: {p['kind']}; target: {p['target_playbook'] or '-'} -->\n"
    )
    out = config.PROPOSALS_DIR / "approved" / f"{slug}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(header + body)
    return config.rel(out)


def apply_decision(run: dict, gate_id: str, decision: Decision) -> Gate:
    gates = [Gate(**g) for g in run["gates"]]
    gate = next((g for g in gates if g.gate_id == gate_id), None)
    if gate is None:
        raise KeyError(gate_id)
    if gate.status != "pending":
        raise ValueError(f"Gate {gate_id} was already decided")

    gate.status = {"approve": "approved", "deny": "denied", "modify": "modified"}[decision.decision]
    gate.decision = {**decision.model_dump(), "decided_at": datetime.now(timezone.utc).isoformat()}
    if gate.kind == "playbook_proposal" and decision.decision != "deny":
        gate.decision["written_to"] = write_approved_proposal(run["run_id"], gate, decision)

    run["gates"] = [g.model_dump() for g in gates]
    run["final_action"] = final_action(run)
    run["status"] = run_status(run)
    return gate


def final_action(run: dict) -> dict:
    """The action that stands after human decisions."""
    inv = run.get("investigation")
    if not inv:
        return {"action": None, "by": None, "note": "No investigation"}
    for g in run["gates"]:
        if g["kind"] not in ("action_approval", "act_then_confirm") or g["status"] == "pending":
            continue
        d = g["decision"]
        if g["status"] == "denied":
            return {"action": None, "by": d["reviewer"], "note": f"Rejected: {d['reason'] or 'no reason given'}"}
        if g["status"] == "modified" and d.get("action_override"):
            return {"action": d["action_override"], "by": d["reviewer"], "note": d["reason"]}
        return {"action": inv["recommended_action"], "by": d["reviewer"], "note": d["reason"]}
    pending = any(g["kind"] == "action_approval" and g["status"] == "pending" for g in run["gates"])
    return {
        "action": None if pending else inv["recommended_action"],
        "by": None if pending else "agent",
        "note": "Awaiting analyst approval" if pending else "Within the agent's autonomous scope",
    }


def run_status(run: dict) -> str:
    if run.get("error"):
        return "failed"
    if any(g["blocking"] and g["status"] == "pending" for g in run["gates"]):
        return "awaiting_human"
    if any(g["status"] == "pending" for g in run["gates"]):
        return "completed_with_followups"
    return "completed"
