"""Alert simulator.

Synthesizes new alerts from the columns of synthetic_alerts.csv: it reuses the
CSV's description templates with fresh users, hosts, severities and sources drawn
from the CSV's own value distributions (so the same field noise carries over).
A share of alerts are of types no playbook covers, to exercise the novelty path
and playbook proposals.
"""

import json
import random
import re
from datetime import datetime, timedelta, timezone

from . import config
from .data import load_csv_alerts
from .models import Alert

NOVEL_TEMPLATES = [
    "Cryptominer process xmrig consuming 97% CPU on {device} for {hours}h, with outbound connections to a mining pool on port 3333.",
    "Cloud storage bucket finance-exports-{n} was changed to public-read by {user}; {n} objects are now internet-accessible.",
    "OAuth application 'Mail Helper {n}' was granted Mail.ReadWrite and offline_access consent by {user} from an unverified publisher.",
    "Unsigned kernel driver loaded on {device} immediately after a USB HID device enumerated as a keyboard.",
]


def _swap_entities(text: str, rng: random.Random, user: str, device: str) -> str:
    text = re.sub(r"\bjdoe\d+\b", user, text)
    text = re.sub(r"\b(WKS|SRV)-\d+\b", device, text)
    # Rescale standalone counts; leave IPs, CVE IDs and host IDs alone.
    return re.sub(r"(?<![.\-])\b\d{2,4}\b(?![.\-]\d)", lambda m: str(max(2, int(int(m.group()) * rng.uniform(0.6, 1.6)))), text)


def generate(count: int = 10, novel_ratio: float = 0.2, seed: int | None = None) -> list[Alert]:
    rng = random.Random(seed)
    source = load_csv_alerts()
    severities = [a.severity for a in source]
    systems = [a.source_system for a in source]
    start = datetime.now(timezone.utc)
    existing = _load()
    next_id = 1 + max((int(a["alert_id"].split("-")[1]) for a in existing), default=0)

    alerts = []
    for i in range(count):
        user = f"jdoe{rng.randint(1, 60)}"
        device = f"WKS-{rng.randint(1000, 9999)}"
        # Keep the CSV's quirk: the description's entities don't always match the fields.
        field_user = user if rng.random() < 0.6 else f"jdoe{rng.randint(1, 60)}"
        field_device = device if rng.random() < 0.6 else f"WKS-{rng.randint(1000, 9999)}"
        if rng.random() < novel_ratio:
            description = rng.choice(NOVEL_TEMPLATES).format(device=device, user=user, n=rng.randint(10, 999), hours=rng.randint(2, 30))
        else:
            description = _swap_entities(rng.choice(source).description, rng, user, device)
        alerts.append(Alert(
            alert_id=f"SIM-{next_id + i:04d}",
            timestamp=(start - timedelta(minutes=rng.randint(0, 600))).strftime("%Y-%m-%dT%H:%M:00Z"),
            severity=rng.choice(severities),
            source_system=rng.choice(systems),
            affected_user=field_user,
            affected_device=field_device,
            description=description,
            origin="simulator",
        ))

    _save(existing + [a.model_dump() for a in alerts])
    return alerts


def _load() -> list[dict]:
    return json.loads(config.SIM_ALERTS.read_text()) if config.SIM_ALERTS.exists() else []


def _save(alerts: list[dict]) -> None:
    config.SIM_ALERTS.parent.mkdir(parents=True, exist_ok=True)
    config.SIM_ALERTS.write_text(json.dumps(alerts, indent=2))


def clear() -> None:
    config.SIM_ALERTS.unlink(missing_ok=True)
