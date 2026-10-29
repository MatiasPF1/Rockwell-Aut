"""Data shapes shared across the pipeline, the LLM contract, and the API."""

from typing import Literal, Optional

from pydantic import BaseModel, Field

Severity = Literal["Low", "Medium", "High", "Critical"]
Action = Literal["monitor", "isolate", "escalate", "close"]
SEVERITY_ORDER: list[str] = ["Low", "Medium", "High", "Critical"]


class Alert(BaseModel):
    alert_id: str
    timestamp: str
    severity: str
    source_system: str
    affected_user: str
    affected_device: str
    description: str
    origin: Literal["csv", "simulator"] = "csv"


class Incident(BaseModel):
    incident_id: str
    alert_type: str
    circumstances: str
    resolution: str
    outcome: str


class IncidentMatch(BaseModel):
    incident: Incident
    score: float = Field(ge=0, le=1)
    method: str


class Playbook(BaseModel):
    slug: str
    path: str
    title: str
    alert_type: str
    attack_mapping: str
    sections: dict[str, str]
    text: str
    origin: Literal["official", "ai_drafted_human_approved"] = "official"


class StepRule(BaseModel):
    """A label from config/playbook_steps.yaml saying who owns a playbook step."""

    playbook: str
    match: str
    owner: Literal["agent", "human"]
    gate: Literal["none", "blocking", "act_then_confirm"] = "none"
    constraint: Optional[str] = None
    note: str = ""


class QualityFlag(BaseModel):
    code: str
    message: str
    penalty: int  # confidence points removed


# ---- What the model must return (structured output) ----


class StepResult(BaseModel):
    phase: Literal["Detection", "Analysis", "Containment"]
    playbook: str = Field(description="Slug of the playbook this step comes from")
    playbook_quote: str = Field(description="The playbook sentence this step follows, copied verbatim")
    owner: Literal["agent", "human"]
    status: Literal["completed", "evidence_unavailable", "needs_human", "not_applicable"]
    finding: str
    evidence: list[str] = Field(description="Alert fields or incident IDs this finding rests on")


class PlaybookProposal(BaseModel):
    kind: Literal["new_playbook", "addendum"]
    target_playbook: Optional[str] = Field(description="Existing playbook slug for an addendum, else null")
    title: str
    rationale: str
    markdown: str


class Investigation(BaseModel):
    incident_type: str
    classification_rationale: str
    assessed_severity: Severity
    severity_rationale: str
    recommended_action: Action
    action_rationale: str
    next_actions: list[str]
    steps: list[StepResult]
    evidence_gaps: list[str]
    related_incident_ids: list[str]
    model_confidence: int = Field(description="Self-reported 0-100; weighted lightly")
    is_novel: bool
    playbook_proposal: Optional[PlaybookProposal]


# ---- Human-in-the-loop ----


class Gate(BaseModel):
    gate_id: str
    kind: Literal["action_approval", "act_then_confirm", "playbook_step", "playbook_proposal"]
    title: str
    reason: str
    blocking: bool
    payload: dict = {}
    status: Literal["pending", "approved", "denied", "modified"] = "pending"
    decision: Optional[dict] = None


class Decision(BaseModel):
    decision: Literal["approve", "deny", "modify"]
    reviewer: str = "analyst"
    reason: str = ""
    edited_markdown: Optional[str] = None  # playbook proposals
    action_override: Optional[Action] = None  # action approvals
