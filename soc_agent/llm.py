"""The model call that performs the L1 investigation.

Prompt layout is built for prompt caching: the stable instructions and the full
playbook knowledge base come first and are cached; only the per-alert request
varies. `usage.cache_read_input_tokens` on the trace shows the reuse.
"""

import json
from dataclasses import dataclass, field
from typing import Protocol

import anthropic

from . import config
from .models import Alert, IncidentMatch, Investigation, Playbook, PlaybookProposal, QualityFlag, StepResult, StepRule
from .playbooks import L1_PHASES, build_index

SYSTEM_PROMPT = """\
You are a Level 1 SOC analyst assistant. You triage one security alert at a time
and hand a recommendation to a human analyst. You do not execute actions; you
recommend them, and a human approves anything that changes production systems.

Your scope is Level 1: the NIST Detection and Analysis phases, ending in a
Containment recommendation. Eradication, Recovery and Lessons Learned belong to
Level 2 and are out of scope - do not produce steps for them.

How to work:
1. Classify the incident type using the playbook triggers in the knowledge base.
   Retrieved historical incidents are evidence, not the answer: if the alert
   text points elsewhere, say so and classify by the alert text. If no playbook
   fits, use the type name you think is right and set is_novel to true.
2. Assess severity from what the alert describes. The reported severity and
   source system in alerts are often wrong; judge by content and explain any
   change.
3. Work through the Detection, Analysis and Containment sections of the selected
   playbook(s). Produce one step per playbook instruction you act on, quoting
   that instruction verbatim in playbook_quote.
4. You only have the alert record and the retrieved historical incidents. You
   cannot query logs, EDR, mail gateways, ticketing or people. When a step needs
   data you do not have, set status to evidence_unavailable and say what data
   would settle it. Never invent log lines, hashes, ticket numbers or results.
5. Steps the request lists as human-owned get owner "human" and status
   needs_human; describe what the analyst must find out. Respect every listed
   constraint (for example: never recommend contacting the user).
6. Recommend exactly one action:
   - monitor: real but low-risk or already blocked; keep watching
   - isolate: contain a host, account or session now
   - escalate: needs Level 2, Legal/HR, or a decision beyond Level 1
   - close: benign, duplicate, or false positive
7. evidence lists must cite alert fields (for example alert.description) or
   incident IDs (for example INC-2014).
8. model_confidence is your honest 0-100 estimate that the classification and
   action are right.
9. Propose a playbook change only when is_novel is true (new_playbook) or the
   selected playbook clearly misses something this alert needs (addendum). Write
   proposals in the same structure as the existing playbooks (Trigger line,
   ## Detection, ## Analysis, ## Containment, ## Eradication, ## Recovery,
   ## Lessons Learned). Do not invent ATT&CK IDs you are unsure of. Otherwise
   set playbook_proposal to null.
"""


@dataclass
class InvestigationRequest:
    alert: Alert
    flags: list[QualityFlag]
    matches: list[IncidentMatch]
    selected: list[Playbook]
    rules: list[StepRule]
    knowledge_base: dict[str, Playbook] = field(repr=False, default_factory=dict)


@dataclass
class LLMResult:
    investigation: Investigation
    model: str
    usage: dict
    reasoning_summary: str = ""
    request_id: str | None = None


class LLMError(RuntimeError):
    pass


class LLM(Protocol):
    name: str

    def investigate(self, req: InvestigationRequest) -> LLMResult: ...


def knowledge_base_text(books: dict[str, Playbook]) -> str:
    parts = [build_index(books)]
    for slug, book in books.items():
        label = "OFFICIAL" if book.origin == "official" else "AI-DRAFTED, HUMAN-APPROVED"
        parts.append(f'<playbook slug="{slug}" origin="{label}">\n{book.text}\n</playbook>')
    return "\n\n".join(parts)


def request_text(req: InvestigationRequest) -> str:
    body = {
        "alert": req.alert.model_dump(exclude={"origin"}),
        "data_quality_flags": [f.model_dump() for f in req.flags],
        "retrieved_historical_incidents": [
            {**m.incident.model_dump(), "similarity": m.score} for m in req.matches
        ],
        "selected_playbooks": [b.slug for b in req.selected] or "none - no playbook matched",
        "human_owned_steps_and_constraints": [r.model_dump() for r in req.rules],
    }
    return (
        "Investigate this alert. Playbooks were selected from the alert types of the "
        "retrieved historical incidents.\n\n" + json.dumps(body, indent=2)
    )


class ClaudeLLM:
    name = "claude"

    def __init__(self, client: anthropic.Anthropic | None = None, model: str = config.MODEL):
        self.client = client or anthropic.Anthropic()
        self.model = model

    def investigate(self, req: InvestigationRequest) -> LLMResult:
        try:
            response = self.client.beta.messages.parse(
                model=self.model,
                max_tokens=16000,
                # Opt-in: if a safety classifier declines (cyber content is common
                # here), the API reruns on a fallback model instead of stopping.
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                thinking={"type": "adaptive", "display": "summarized"},
                output_config={"effort": config.EFFORT},
                system=[
                    {"type": "text", "text": SYSTEM_PROMPT},
                    {
                        "type": "text",
                        "text": knowledge_base_text(req.knowledge_base),
                        "cache_control": {"type": "ephemeral"},
                    },
                ],
                messages=[{"role": "user", "content": request_text(req)}],
                output_format=Investigation,
            )
        except anthropic.AuthenticationError as e:
            raise LLMError("No valid Anthropic credentials. Set ANTHROPIC_API_KEY, or run with SOC_AGENT_LLM=mock.") from e
        except anthropic.APIStatusError as e:
            raise LLMError(f"Claude API error {e.status_code}: {e.message}") from e
        except anthropic.APIConnectionError as e:
            raise LLMError(f"Could not reach the Claude API: {e}") from e

        if response.stop_reason == "refusal":
            category = response.stop_details.category if response.stop_details else None
            raise LLMError(f"Model declined to answer (category: {category})")
        if response.stop_reason == "max_tokens":
            raise LLMError("Model ran out of output tokens before finishing")
        if response.parsed_output is None:
            raise LLMError("Model returned no structured investigation")

        usage = response.usage
        return LLMResult(
            investigation=response.parsed_output,
            model=response.model,
            usage={
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "cache_read_input_tokens": usage.cache_read_input_tokens or 0,
                "cache_creation_input_tokens": usage.cache_creation_input_tokens or 0,
            },
            reasoning_summary="\n\n".join(b.thinking for b in response.content if b.type == "thinking" and b.thinking),
            request_id=response._request_id,
        )


# Recommended action by type for the offline stand-in.
_MOCK_ACTIONS = {
    "Ransomware Indicator": "isolate", "Malware": "isolate", "C2 Beaconing": "isolate",
    "Insider Threat": "escalate", "Data Exfiltration": "escalate", "Privilege Escalation": "escalate",
    "Suspicious Login": "isolate", "Phishing": "monitor", "Brute Force": "monitor",
    "Vulnerability": "monitor", "Web Application Attack": "monitor", "DDoS": "escalate",
}


class MockLLM:
    """Deterministic offline stand-in so the pipeline and UI run without an API key.

    It never reasons about the alert: it follows the selected playbook and fills in
    template findings. The trace records backend "mock" for every run it produces.
    """

    name = "mock"

    def investigate(self, req: InvestigationRequest) -> LLMResult:
        primary = req.selected[0] if req.selected else None
        incident_type = primary.alert_type if primary else "Unclassified"
        steps: list[StepResult] = []
        for book in req.selected:
            for phase in L1_PHASES:
                text = book.sections.get(phase, "")
                if not text:
                    continue
                quote = text.split(". ")[0].rstrip(".") + "."
                human = next((r for r in req.rules if r.playbook == book.slug and r.owner == "human" and r.match in text), None)
                if human:
                    steps.append(StepResult(phase=phase, playbook=book.slug, playbook_quote=human.match, owner="human",
                                            status="needs_human", finding=f"Analyst to do: {human.note or human.match}",
                                            evidence=["alert.description"]))
                steps.append(StepResult(
                    phase=phase, playbook=book.slug, playbook_quote=quote, owner="agent",
                    status="completed" if phase == "Detection" else "evidence_unavailable",
                    finding="The alert matches this playbook's detection pattern." if phase == "Detection"
                    else "Needs log or system data that is not connected yet.",
                    evidence=["alert.description", *[m.incident.incident_id for m in req.matches[:1]]],
                ))

        proposal = None
        if primary is None:
            proposal = PlaybookProposal(
                kind="new_playbook", target_playbook=None, title="Unclassified alert type",
                rationale="No existing playbook covers this alert type.",
                markdown=(
                    "# Playbook: Unclassified Alert\nTrigger: alert_type = Unclassified\n\n"
                    "## Detection\nDescribe the signal that fires this alert and which system reports it.\n\n"
                    "## Analysis\nList what to confirm before acting, and which data answers each question.\n\n"
                    "## Containment\nState the first containment step and who approves it.\n\n"
                    "## Eradication\nDescribe how to remove the cause.\n\n"
                    "## Recovery\nDescribe how to return to normal operation.\n\n"
                    "## Lessons Learned\nRecord what would have caught this sooner.\n"
                ),
            )

        inv = Investigation(
            incident_type=incident_type,
            classification_rationale=(
                f"Matches the alert type of the closest historical incident ({req.matches[0].incident.incident_id})."
                if primary and req.matches else "No historical incident matched closely enough to assign a type."
            ),
            assessed_severity=req.alert.severity if req.alert.severity in ("Low", "Medium", "High", "Critical") else "Medium",
            severity_rationale="Kept the reported severity.",
            recommended_action=_MOCK_ACTIONS.get(incident_type, "escalate"),
            action_rationale=f"Standard Level 1 response for {incident_type} alerts." if primary
            else "An analyst needs to classify this alert before any action is taken.",
            next_actions=[f"Work through the Analysis section of {primary.slug}.", "Confirm the affected user and device against the alert record."]
            if primary else ["Classify the alert and review the drafted playbook."],
            steps=steps,
            evidence_gaps=["Log, EDR, mail-gateway and ticketing data are not connected, so steps that need them could not be checked."],
            related_incident_ids=[m.incident.incident_id for m in req.matches],
            model_confidence=70 if primary else 30,
            is_novel=primary is None,
            playbook_proposal=proposal,
        )
        return LLMResult(investigation=inv, model="mock", usage={})


def get_llm() -> LLM:
    return MockLLM() if config.LLM_BACKEND == "mock" else ClaudeLLM()
