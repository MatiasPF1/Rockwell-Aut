"""JSON-file persistence for runs (one file per run under var/runs/)."""

import json
import threading

from . import config

_lock = threading.Lock()


def save(run: dict) -> None:
    config.RUNS_DIR.mkdir(parents=True, exist_ok=True)
    path = config.RUNS_DIR / f"{run['run_id']}.json"
    with _lock:
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(run, indent=2, default=str))
        tmp.replace(path)


def load(run_id: str) -> dict:
    path = config.RUNS_DIR / f"{run_id}.json"
    if not path.exists():
        raise KeyError(run_id)
    return json.loads(path.read_text())


def list_runs() -> list[dict]:
    if not config.RUNS_DIR.exists():
        return []
    runs = [json.loads(p.read_text()) for p in config.RUNS_DIR.glob("*.json")]
    return sorted(runs, key=lambda r: r["created_at"], reverse=True)
