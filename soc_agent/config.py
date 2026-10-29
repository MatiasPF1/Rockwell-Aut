"""Paths, model settings, and tunable thresholds in one place."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ALERTS_CSV = ROOT / "synthetic_alerts.csv"
INCIDENTS_CSV = ROOT / "historical_incidents.csv"
PLAYBOOK_DIR = ROOT / "Playbooks"  # the agent never writes here; analysts can edit from the UI
PLAYBOOK_HISTORY = ROOT / "playbook_history"  # previous versions, saved before every UI edit
PLAYBOOK_STEPS = ROOT / "config" / "playbook_steps.yaml"
PLAYBOOK_INDEX = ROOT / "knowledge" / "playbook_index.md"
PROPOSALS_DIR = ROOT / "playbook_proposals"  # human-approved AI drafts live here
STATE_DIR = ROOT / "var"
RUNS_DIR = STATE_DIR / "runs"
SIM_ALERTS = STATE_DIR / "simulated_alerts.json"

MODEL = os.environ.get("SOC_AGENT_MODEL", "claude-opus-5-5")
EFFORT = os.environ.get("SOC_AGENT_EFFORT", "high")
# "claude" calls the API; "mock" runs a deterministic offline stand-in for dev/tests.
LLM_BACKEND = os.environ.get("SOC_AGENT_LLM", "claude")

# How many historical incidents retrieval returns.
RETRIEVAL_TOP_K = 3
# A second playbook is consulted when its aggregated score is within this ratio of the top one.
SECONDARY_PLAYBOOK_RATIO = 0.8
# Below this best-match score the alert is treated as something we haven't seen before.
NOVELTY_THRESHOLD = 0.25
# Runs below this confidence always go to an analyst, whatever the action.
LOW_CONFIDENCE_THRESHOLD = 60
# Auto-close is only allowed at or above this confidence.
AUTO_CLOSE_CONFIDENCE = 85


def rel(path: Path) -> str:
    """Repo-relative path for display; absolute if outside the repo."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)
