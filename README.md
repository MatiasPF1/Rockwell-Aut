# SOC L1 Triage Agent (MVP)

An AI Level 1 investigation assistant. It takes one alert, finds similar
historical incidents, picks the playbook(s) those incidents point to, works the
playbook's Detection / Analysis / Containment steps, and produces a report with a
full, clickable investigation trace. People approve anything that matters.

## Run it

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
export ANTHROPIC_API_KEY=...            # or SOC_AGENT_LLM=mock to run offline
.venv/bin/uvicorn soc_agent.server:app --reload
# open http://127.0.0.1:8000
```

Tests (use the offline mock, never the API): `.venv/bin/python -m pytest`

Regenerate the playbook index after playbooks change: `.venv/bin/python -m soc_agent.index`

| Env var | Default | |
|---|---|---|
| `SOC_AGENT_LLM` | `claude` | `mock` = deterministic offline stand-in (no API calls; the trace records `backend: mock`) |
| `SOC_AGENT_MODEL` | `claude-opus-5-5` | |
| `SOC_AGENT_EFFORT` | `high` | `low` / `medium` / `high` / `xhigh` / `max` |

## Pipeline

```
alert ─► data_quality.pre ─► retrieve_historical_incidents ─► select_playbooks
      ─► llm.investigate (one span per playbook step) ─► data_quality.post
      ─► confidence ─► hitl.policy ─► human gates ─► report
```

Every stage is a span in the trace (`soc_agent/trace.py`), shown in the UI as a
waterfall like an APM trace. Human decisions are spans too, so time spent waiting
on an analyst is visible.

| Module | Role |
|---|---|
| `retrieval.py` | **Seam for the real retriever.** `IncidentRetriever` protocol + a crude `PlaceholderRetriever` so the pipeline runs. Plug the BM25 + semantic retriever in with `set_retriever()`. |
| `pipeline.py` | Orchestration; playbook choice = summed similarity per incident `alert_type`, plus a second playbook when the runner-up is within 80%. Matches below 0.25 pick no playbook and the alert is handled as novel. |
| `llm.py` | One structured-output call to Claude. System prompt + full playbook knowledge base are prompt-cached; the trace shows cache read/write tokens. Server-side refusal fallback is on. |
| `quality.py` | Code-only checks: user/device in description vs. fields, multi-event alerts, severity conflict, implausible source system, disagreement with history. |
| `confidence.py` | Score from checkable signals; the model's self-rating is only 20%. Novel alerts get the "Based on what I've seen…" preface. |
| `hitl.py` | Which runs need a person, and applying their decisions. |
| `simulator.py` | Synthesizes alerts from the CSV's columns, including types no playbook covers. |
| `server.py` + `web/` | Local web app: queue, trace, approvals, report. |

## Human in the loop

| Gate | When | Blocks? |
|---|---|---|
| Action approval | isolate / escalate; close unless Low-Medium at ≥85 confidence; any run under 60 confidence; severity downgraded 2+ levels | yes |
| Act then confirm | isolate where the playbook says act immediately (ransomware, malware) and confidence is fine | no |
| Playbook step | a step `config/playbook_steps.yaml` marks as human-owned, in the L1 phases | yes |
| Playbook proposal | agent drafted a new playbook or addendum: approve, deny, or edit then approve | no |

The agent never writes to `Playbooks/`. Analysts can edit a playbook from the
report (Playbooks consulted → click one → Edit); each save first copies the
previous version to `playbook_history/<name>/` and refuses to overwrite a newer
save. Approved drafts are written to
`playbook_proposals/approved/` with an AI-drafted header and loaded next to the
official playbooks on later runs. The human/agent split lives in
`config/playbook_steps.yaml`, matched by quoting playbook text; the app reports
when a quote no longer matches.

Runs are stored as JSON in `var/runs/` (git-ignored).
