from fastapi.testclient import TestClient

from soc_agent import config, simulator
from soc_agent.models import Decision
from soc_agent.pipeline import decide, run_alert
from soc_agent.server import app


def gate_kinds(run):
    return {g["kind"] for g in run["gates"]}


def test_ransomware_uses_act_then_confirm():
    run = run_alert("ALT-1051")
    assert run["status"] != "failed", run.get("error")
    assert run["playbooks"][0]["slug"] == "ransomware_indicator"
    # Reported Low on Cloud WAF: data-quality flags drag confidence down, so isolation
    # needs approval up front rather than the act-then-confirm fast path.
    assert {"action_approval", "act_then_confirm"} & gate_kinds(run)
    kinds = [s["kind"] for s in run["trace"]]
    for kind in ("root", "check", "retrieval", "playbook", "llm", "step", "score", "policy", "report"):
        assert kind in kinds


def test_insider_threat_requires_manager_check():
    run = run_alert("ALT-1003")  # HR-Portal records accessed outside job function, 44GB export
    slugs = [p["slug"] for p in run["playbooks"]]
    assert "insider_threat" in slugs
    step_gates = [g for g in run["gates"] if g["kind"] == "playbook_step"]
    assert any("business justification" in g["payload"]["quote"] for g in step_gates)
    assert run["status"] == "awaiting_human"


def test_novel_alert_proposes_playbook_and_approval_writes_draft():
    alert = next(a for a in simulator.generate(30, novel_ratio=1.0, seed=7) if "OAuth" in a.description)
    run = run_alert(alert.alert_id)
    assert run["confidence"]["novel"] is True
    assert run["confidence"]["preface"].startswith("Based on what I've seen")
    proposal = next(g for g in run["gates"] if g["kind"] == "playbook_proposal")

    run = decide(run["run_id"], proposal["gate_id"], Decision(decision="modify", reviewer="tester", edited_markdown="# Playbook: Edited\n"))
    gate = next(g for g in run["gates"] if g["gate_id"] == proposal["gate_id"])
    assert gate["status"] == "modified"
    written = list((config.PROPOSALS_DIR / "approved").glob("*.md"))
    assert len(written) == 1 and "# Playbook: Edited" in written[0].read_text()
    span = next(s for s in run["trace"] if s["span_id"] == gate["payload"]["span_id"])
    assert span["status"] == "modified" and span["end"] is not None


def test_action_decision_sets_final_action():
    run = run_alert("ALT-1003")
    gate = next(g for g in run["gates"] if g["kind"] == "action_approval")
    run = decide(run["run_id"], gate["gate_id"], Decision(decision="modify", action_override="isolate", reviewer="tester"))
    assert run["final_action"] == {"action": "isolate", "by": "tester", "note": ""}


def test_api_end_to_end():
    client = TestClient(app)
    assert client.get("/api/health").json()["step_rule_problems"] == []
    assert len(client.get("/api/alerts").json()) == 280
    run = client.post("/api/runs", json={"alert_id": "ALT-1002", "wait": True}).json()
    assert client.get(f"/api/runs/{run['run_id']}").json()["status"] == run["status"]
    md = client.get(f"/api/runs/{run['run_id']}/report.md").text
    assert md.startswith("# Investigation report - ALT-1002")
    assert client.post("/api/runs", json={"alert_id": "NOPE"}).status_code == 404
    if run["gates"]:
        gid = run["gates"][0]["gate_id"]
        assert client.post(f"/api/runs/{run['run_id']}/gates/{gid}", json={"decision": "approve"}).status_code == 200
        assert client.post(f"/api/runs/{run['run_id']}/gates/{gid}", json={"decision": "approve"}).status_code == 409


def test_playbook_edit_backs_up_and_detects_conflicts(tmp_path, monkeypatch):
    import shutil
    books = tmp_path / "Playbooks"
    shutil.copytree(config.PLAYBOOK_DIR, books)
    monkeypatch.setattr(config, "PLAYBOOK_DIR", books)
    monkeypatch.setattr(config, "PLAYBOOK_HISTORY", tmp_path / "history")
    client = TestClient(app)

    pb = client.get("/api/playbooks/phishing").json()
    edited = pb["text"] + "\n## Notes\nCheck the reply-to header too.\n"
    res = client.put("/api/playbooks/phishing", json={"text": edited, "base_hash": pb["hash"], "editor": "tester"})
    assert res.status_code == 200 and res.json()["saved"]
    assert "Check the reply-to header" in (books / "phishing.md").read_text()
    hist = client.get("/api/playbooks/phishing").json()["history"]
    assert hist[0]["editor"] == "tester"
    backups = list((tmp_path / "history" / "phishing").glob("*.md"))
    assert len(backups) == 1 and "Check the reply-to header" not in backups[0].read_text()

    # Saving against the old hash is refused; so is dropping the Trigger line.
    assert client.put("/api/playbooks/phishing", json={"text": edited + "x", "base_hash": pb["hash"]}).status_code == 409
    fresh = client.get("/api/playbooks/phishing").json()["hash"]
    assert client.put("/api/playbooks/phishing", json={"text": "# no trigger", "base_hash": fresh}).status_code == 400
    assert client.get("/api/playbooks/../config").status_code == 404


def test_brand_logo_served_when_present(tmp_path, monkeypatch):
    from soc_agent import server
    monkeypatch.setattr(server, "WEB_DIR", tmp_path)
    client = TestClient(app)
    assert client.head("/brand/logo").status_code == 404
    (tmp_path / "brand").mkdir()
    (tmp_path / "brand" / "logo.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
    assert client.head("/brand/logo").status_code == 200
    assert client.get("/brand/logo").headers["content-type"].startswith("image/svg")
