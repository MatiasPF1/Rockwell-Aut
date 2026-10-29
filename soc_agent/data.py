"""Loaders for the alert and incident CSVs plus simulator output."""

import csv
import json
from functools import lru_cache

from . import config
from .models import Alert, Incident


@lru_cache(maxsize=1)
def load_csv_alerts() -> tuple[Alert, ...]:
    with open(config.ALERTS_CSV, newline="") as f:
        return tuple(Alert(**row) for row in csv.DictReader(f))


@lru_cache(maxsize=1)
def load_incidents() -> tuple[Incident, ...]:
    with open(config.INCIDENTS_CSV, newline="") as f:
        return tuple(Incident(**row) for row in csv.DictReader(f))


def load_simulated_alerts() -> list[Alert]:
    if not config.SIM_ALERTS.exists():
        return []
    return [Alert(**a) for a in json.loads(config.SIM_ALERTS.read_text())]


def all_alerts() -> list[Alert]:
    return [*load_simulated_alerts(), *load_csv_alerts()]


def get_alert(alert_id: str) -> Alert:
    for alert in all_alerts():
        if alert.alert_id == alert_id:
            return alert
    raise KeyError(alert_id)
