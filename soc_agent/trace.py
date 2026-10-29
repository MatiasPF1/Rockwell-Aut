"""Span-based investigation trail, modelled on APM traces.

One run is one trace; each pipeline step, model call, playbook step and human
decision is a span with inputs, outputs and timing. The web UI draws these as a
waterfall. Spans are plain dicts so the whole run serializes to JSON.
"""

import time
import uuid
from contextlib import contextmanager
from typing import Any, Callable, Iterator, Optional


def now_ms() -> float:
    return round(time.time() * 1000, 1)


class Tracer:
    def __init__(self, on_change: Optional[Callable[[], None]] = None):
        self.spans: list[dict] = []
        self._stack: list[str] = []
        self._on_change = on_change or (lambda: None)

    def start(self, name: str, kind: str, parent_id: Optional[str] = None, **attributes: Any) -> dict:
        span = {
            "span_id": uuid.uuid4().hex[:12],
            "parent_id": parent_id if parent_id is not None else (self._stack[-1] if self._stack else None),
            "name": name,
            "kind": kind,
            "start": now_ms(),
            "end": None,
            "status": "running",
            "attributes": attributes,
            "input": None,
            "output": None,
        }
        self.spans.append(span)
        self._on_change()
        return span

    def finish(self, span: dict, status: str = "ok", output: Any = None) -> None:
        span["end"] = now_ms()
        span["status"] = status
        if output is not None:
            span["output"] = output
        self._on_change()

    @contextmanager
    def span(self, name: str, kind: str, **attributes: Any) -> Iterator[dict]:
        span = self.start(name, kind, **attributes)
        self._stack.append(span["span_id"])
        try:
            yield span
        except Exception as exc:
            span["attributes"]["error"] = f"{type(exc).__name__}: {exc}"
            self.finish(span, status="error")
            raise
        else:
            self.finish(span, status=span["status"] if span["status"] != "running" else "ok")
        finally:
            self._stack.pop()

    def event(self, name: str, kind: str, output: Any = None, **attributes: Any) -> dict:
        """A zero-duration span under the current span."""
        span = self.start(name, kind, **attributes)
        self.finish(span, output=output)
        return span


def find_span(spans: list[dict], span_id: str) -> dict:
    return next(s for s in spans if s["span_id"] == span_id)
