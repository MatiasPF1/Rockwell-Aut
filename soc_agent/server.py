"""Local web app: alert queue, live investigation trace, approvals, and reports.

Run: `uvicorn soc_agent.server:app --reload` then open http://127.0.0.1:8000
"""

import threading

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import config, pipeline, report, simulator, store
from .data import all_alerts
from .models import Decision
from .playbooks import (
    PlaybookConflict, content_hash, history, load_playbooks, rules_for, save_playbook, validate_step_rules,
)
from .retrieval import get_retriever

WEB_DIR = config.ROOT / "web"

app = FastAPI(title="SOC L1 Triage Agent")


class RunRequest(BaseModel):
    alert_id: str
    wait: bool = False  # tests and scripts can block until the run finishes


class SimulateRequest(BaseModel):
    count: int = 10
    novel_ratio: float = 0.2
    seed: int | None = None


@app.get("/api/health")
def health() -> dict:
    return {
        "llm_backend": config.LLM_BACKEND,
        "model": config.MODEL if config.LLM_BACKEND == "claude" else "mock",
        "retriever": get_retriever().name,
        "playbooks": len(load_playbooks()),
        "step_rule_problems": validate_step_rules(),
    }


@app.get("/api/alerts")
def alerts(q: str = "", origin: str = "") -> list[dict]:
    latest: dict[str, dict] = {}
    for run in store.list_runs():  # newest first
        latest.setdefault(run["alert"]["alert_id"], run)
    out = []
    for a in all_alerts():
        if origin and a.origin != origin:
            continue
        if q and q.lower() not in f"{a.alert_id} {a.description} {a.source_system}".lower():
            continue
        run = latest.get(a.alert_id)
        out.append({**a.model_dump(), "last_run": {"run_id": run["run_id"], "status": run["status"]} if run else None})
    return out


@app.post("/api/simulate")
def simulate(req: SimulateRequest) -> list[dict]:
    return [a.model_dump() for a in simulator.generate(req.count, req.novel_ratio, req.seed)]


@app.delete("/api/simulate")
def clear_simulated() -> dict:
    simulator.clear()
    return {"ok": True}


@app.post("/api/runs")
def start_run(req: RunRequest) -> dict:
    try:
        run = pipeline.new_run(req.alert_id)
    except KeyError:
        raise HTTPException(404, f"Unknown alert {req.alert_id}")
    if req.wait:
        return pipeline.investigate(run)
    threading.Thread(target=pipeline.investigate, args=(run,), daemon=True).start()
    return run


@app.get("/api/runs")
def runs() -> list[dict]:
    return [
        {k: r.get(k) for k in ("run_id", "created_at", "status")} | {"alert_id": r["alert"]["alert_id"]}
        for r in store.list_runs()
    ]


@app.get("/api/runs/{run_id}")
def get_run(run_id: str) -> dict:
    try:
        return store.load(run_id)
    except KeyError:
        raise HTTPException(404, "Run not found")


@app.get("/api/runs/{run_id}/report.md", response_class=PlainTextResponse)
def get_report_markdown(run_id: str) -> str:
    run = get_run(run_id)
    return report.to_markdown(run.get("report") or report.build(run))


@app.post("/api/runs/{run_id}/gates/{gate_id}")
def decide(run_id: str, gate_id: str, decision: Decision) -> dict:
    try:
        return pipeline.decide(run_id, gate_id, decision)
    except KeyError:
        raise HTTPException(404, "Run or gate not found")
    except ValueError as e:
        raise HTTPException(409, str(e))


class PlaybookSave(BaseModel):
    text: str
    base_hash: str  # hash of the version the editor loaded; protects against overwriting someone else's save
    editor: str = "analyst"
    note: str = ""


@app.get("/api/playbooks/{slug:path}")
def get_playbook(slug: str) -> dict:
    books = load_playbooks()
    if slug not in books:
        raise HTTPException(404, "Playbook not found")
    book = books[slug]
    return {
        **book.model_dump(exclude={"sections"}),
        "hash": content_hash(book.text),
        "history": history(slug),
        "step_rules": [r.model_dump() for r in rules_for(slug)],
    }


@app.put("/api/playbooks/{slug:path}")
def put_playbook(slug: str, req: PlaybookSave) -> dict:
    try:
        result = save_playbook(slug, req.text, req.editor, req.base_hash, req.note)
    except KeyError:
        raise HTTPException(404, "Playbook not found")
    except PlaybookConflict:
        raise HTTPException(409, "This playbook changed since you opened it. Reload to see the latest version.")
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {**result, "playbook": get_playbook(slug)}


@app.get("/api/proposals")
def proposals() -> list[dict]:
    return [
        {"slug": slug, "path": b.path, "alert_type": b.alert_type}
        for slug, b in load_playbooks().items()
        if b.origin != "official"
    ]


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


BRAND_EXTENSIONS = ("svg", "png", "webp", "jpg", "jpeg")


@app.api_route("/brand/logo", methods=["GET", "HEAD"])
def brand_logo() -> FileResponse:
    """The organisation's logo, dropped into web/brand/ as logo.<ext>. 404 means use the built-in mark."""
    for ext in BRAND_EXTENSIONS:
        path = WEB_DIR / "brand" / f"logo.{ext}"
        if path.exists():
            return FileResponse(path)
    raise HTTPException(404, "No logo in web/brand/")


app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")
