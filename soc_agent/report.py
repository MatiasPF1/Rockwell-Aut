"""The investigation report: built from the run, rebuilt after every human decision."""


def build(run: dict) -> dict:
    alert, inv, conf = run["alert"], run.get("investigation"), run.get("confidence")
    llm_spans = [s for s in run["trace"] if s["kind"] == "llm"]
    usage = llm_spans[0]["attributes"].get("usage", {}) if llm_spans else {}

    report = {
        "alert_id": alert["alert_id"],
        "status": run["status"],
        "error": run.get("error"),
        "preface": conf["preface"] if conf else None,
        "incident_type": inv["incident_type"] if inv else None,
        "severity": {
            "reported": alert["severity"],
            "assessed": inv["assessed_severity"] if inv else None,
            "rationale": inv["severity_rationale"] if inv else None,
        },
        "confidence": conf,
        "recommended_action": {
            "action": inv["recommended_action"] if inv else None,
            "rationale": inv["action_rationale"] if inv else None,
        },
        "final_action": run.get("final_action"),
        "next_actions": inv["next_actions"] if inv else [],
        "what_went_wrong": {
            "evidence_gaps": inv["evidence_gaps"] if inv else [],
            "data_quality_flags": run.get("quality_flags", []),
            "policy_violations": run.get("policy_violations", []),
        },
        "playbooks_consulted": run.get("playbooks", []),
        "steps": inv["steps"] if inv else [],
        "historical_incidents": run.get("matches", []),
        "human_decisions": [
            {"gate": g["title"], "kind": g["kind"], "status": g["status"], **(g["decision"] or {})}
            for g in run["gates"]
        ],
        "trace_summary": {
            "spans": len(run["trace"]),
            "llm_backend": run.get("llm_backend"),
            "model": llm_spans[0]["attributes"].get("model") if llm_spans else None,
            "usage": usage,
        },
    }
    return report


def to_markdown(report: dict) -> str:
    sev = report["severity"]
    conf = report["confidence"] or {}
    lines = [f"# Investigation report - {report['alert_id']}", ""]
    if report["error"]:
        lines += [f"**Run failed:** {report['error']}", ""]
    if report["preface"]:
        lines += [f"_{report['preface']}_", ""]
    lines += [
        f"- **Status:** {report['status']}",
        f"- **Incident type:** {report['incident_type']}",
        f"- **Severity:** reported {sev['reported']} -> assessed {sev['assessed']}",
        f"- **Confidence:** {conf.get('score', '-')} ({conf.get('band', '-')})",
        f"- **Recommended action:** {report['recommended_action']['action']}",
        f"- **Final action:** {(report['final_action'] or {}).get('action')} "
        f"(by {(report['final_action'] or {}).get('by')})",
        "",
        "## Why",
        report["recommended_action"]["rationale"] or "-",
        "",
        "## Recommended next actions",
        *[f"- {a}" for a in report["next_actions"]],
        "",
        "## Confidence factors",
        *[f"- {f['factor']}: {f['delta']:+d} - {f['detail']}" for f in conf.get("factors", [])],
        "",
        "## Investigation steps",
        "| Phase | Owner | Status | Playbook step | Finding |",
        "|---|---|---|---|---|",
        *[
            f"| {s['phase']} | {s['owner']} | {s['status']} | `{s['playbook']}`: {s['playbook_quote']} | {s['finding']} |"
            for s in report["steps"]
        ],
        "",
        "## What went wrong",
        *[f"- Evidence gap: {g}" for g in report["what_went_wrong"]["evidence_gaps"]],
        *[f"- Data quality ({f['code']}): {f['message']}" for f in report["what_went_wrong"]["data_quality_flags"]],
        *[f"- Policy: {v}" for v in report["what_went_wrong"]["policy_violations"]],
        "",
        "## Historical incidents",
        *[
            f"- {m['incident']['incident_id']} ({m['incident']['alert_type']}, similarity {m['score']:.2f}): "
            f"{m['incident']['circumstances']} -> {m['incident']['outcome']}"
            for m in report["historical_incidents"]
        ],
        "",
        "## Human decisions",
        *[
            f"- {d['gate']}: **{d['status']}**" + (f" by {d['reviewer']} - {d.get('reason') or ''}" if d.get("reviewer") else "")
            for d in report["human_decisions"]
        ],
    ]
    return "\n".join(lines) + "\n"
