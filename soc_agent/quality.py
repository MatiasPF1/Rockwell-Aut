"""Deterministic data-quality checks.

These run in code, not in the LLM, so they are repeatable and auditable. Each flag
lowers confidence by its penalty. `check_alert` runs before the model sees the
alert; `check_against_investigation` runs after, comparing the model's call with
what the alert and retrieval said.
"""

import re
from datetime import datetime

from .models import SEVERITY_ORDER, Alert, IncidentMatch, Investigation, QualityFlag

EDR, DLP, FW, MAIL = "EDR-Endpoint01", "DLP Gateway", "Firewall-Perimeter", "O365 Email Gateway"
SIEM, VPN, IDP, AD = "SIEM Correlation Rule", "VPN Gateway", "IdP / SSO Provider", "AD Domain Controller"
WAF, IDS = "Cloud WAF", "Network IDS"

# Which sensors could plausibly report each alert type. Heuristic; SIEM correlates
# everything so it is always plausible.
PLAUSIBLE_SOURCES: dict[str, set[str]] = {
    "Phishing": {MAIL},
    "Malware": {EDR},
    "Brute Force": {IDP, AD, VPN, IDS},
    "Vulnerability": {IDS, FW, EDR},
    "Insider Threat": {DLP, EDR, AD},
    "DDoS": {FW, WAF, IDS},
    "Data Exfiltration": {DLP, FW, IDS},
    "Privilege Escalation": {AD, EDR},
    "Ransomware Indicator": {EDR},
    "Suspicious Login": {IDP, VPN, AD},
    "Web Application Attack": {WAF, IDS, FW},
    "C2 Beaconing": {IDS, FW, EDR},
}

USER_RE = re.compile(r"\bjdoe\d+\b")
HOST_RE = re.compile(r"\b(?:WKS|SRV|LAP|DC)-\d+\b")


def check_alert(alert: Alert) -> list[QualityFlag]:
    flags: list[QualityFlag] = []
    for field in ("severity", "source_system", "affected_user", "affected_device", "description"):
        if not getattr(alert, field).strip():
            flags.append(QualityFlag(code="MISSING_FIELD", message=f"`{field}` is empty", penalty=10))

    if alert.severity not in SEVERITY_ORDER:
        flags.append(QualityFlag(code="UNKNOWN_SEVERITY", message=f"Severity `{alert.severity}` is not a known level", penalty=10))

    try:
        datetime.fromisoformat(alert.timestamp.replace("Z", "+00:00"))
    except ValueError:
        flags.append(QualityFlag(code="BAD_TIMESTAMP", message=f"Timestamp `{alert.timestamp}` is not ISO-8601", penalty=5))

    users = set(USER_RE.findall(alert.description))
    if users and alert.affected_user not in users:
        flags.append(QualityFlag(
            code="USER_MISMATCH",
            message=f"Description names {', '.join(sorted(users))} but affected_user is {alert.affected_user}",
            penalty=10,
        ))

    hosts = set(HOST_RE.findall(alert.description))
    if hosts and alert.affected_device not in hosts:
        flags.append(QualityFlag(
            code="DEVICE_MISMATCH",
            message=f"Description names {', '.join(sorted(hosts))} but affected_device is {alert.affected_device}",
            penalty=10,
        ))

    if ", and " in alert.description:
        flags.append(QualityFlag(
            code="MULTI_SIGNAL",
            message="Alert describes more than one event; it may need more than one playbook",
            penalty=5,
        ))
    return flags


def check_against_investigation(
    alert: Alert, matches: list[IncidentMatch], inv: Investigation
) -> list[QualityFlag]:
    flags: list[QualityFlag] = []

    if alert.severity in SEVERITY_ORDER:
        delta = SEVERITY_ORDER.index(inv.assessed_severity) - SEVERITY_ORDER.index(alert.severity)
        if abs(delta) >= 2:
            flags.append(QualityFlag(
                code="SEVERITY_CONFLICT",
                message=f"Reported {alert.severity} but the content reads as {inv.assessed_severity}",
                penalty=15,
            ))
        elif delta:
            flags.append(QualityFlag(
                code="SEVERITY_ADJUSTED",
                message=f"Severity adjusted {alert.severity} -> {inv.assessed_severity}",
                penalty=5,
            ))

    plausible = PLAUSIBLE_SOURCES.get(inv.incident_type)
    if plausible and alert.source_system != SIEM and alert.source_system not in plausible:
        flags.append(QualityFlag(
            code="SOURCE_MISMATCH",
            message=f"{alert.source_system} would not normally report a {inv.incident_type} event",
            penalty=10,
        ))

    history_types = {m.incident.alert_type for m in matches}
    if history_types and inv.incident_type not in history_types:
        flags.append(QualityFlag(
            code="TYPE_DISAGREES_WITH_HISTORY",
            message=f"Classified as {inv.incident_type}; similar past incidents were {', '.join(sorted(history_types))}",
            penalty=15,
        ))
    return flags
