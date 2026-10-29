import pytest

from soc_agent import config


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    """Runs, simulated alerts and approved proposals go to a temp dir, never the repo."""
    monkeypatch.setattr(config, "STATE_DIR", tmp_path / "var")
    monkeypatch.setattr(config, "RUNS_DIR", tmp_path / "var" / "runs")
    monkeypatch.setattr(config, "SIM_ALERTS", tmp_path / "var" / "simulated_alerts.json")
    monkeypatch.setattr(config, "PROPOSALS_DIR", tmp_path / "playbook_proposals")
    monkeypatch.setattr(config, "LLM_BACKEND", "mock")
    yield
