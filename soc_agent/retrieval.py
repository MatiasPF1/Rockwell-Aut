"""Historical-incident retrieval: the seam where the real retriever plugs in.

The pipeline only depends on the `IncidentRetriever` protocol. The real
implementation (BM25 + semantic hybrid) is being built separately; swap it in
via `set_retriever()` or by replacing `PlaceholderRetriever` below.

PlaceholderRetriever exists only so the rest of the pipeline runs end to end.
It is a crude keyword scorer, not the retrieval design - don't tune it.
"""

import re
from typing import Protocol, Sequence

from .models import Alert, Incident, IncidentMatch


class IncidentRetriever(Protocol):
    name: str

    def retrieve(
        self, alert: Alert, incidents: Sequence[Incident], k: int
    ) -> list[IncidentMatch]:
        """Return up to k incidents most similar to the alert.

        Contract: sorted best-first, `score` normalized to [0, 1], and an empty
        list (or low scores) when nothing is a good match - the pipeline treats
        that as a never-seen-before alert rather than forcing a match.
        """
        ...


# TODO(retrieval): replace with the BM25 + semantic retriever.
_PLACEHOLDER_CUES: dict[str, tuple[str, ...]] = {
    "Phishing": ("phishing", "spoofed sender", "lookalike domain", "email", "url reputation", "macro"),
    "Malware": ("antivirus", "trojan", "malware signature", "process injection", "quarantined"),
    "Brute Force": ("failed login", "password-spray", "lockout", "failed authentication", "failed connection attempts"),
    "Vulnerability": ("cve-", "cvss", "unpatched", "overdue for patching", "vulnerable"),
    "Insider Threat": ("outside their normal job", "printed", "resignation", "removable", "usb"),
    "DDoS": ("traffic increase", "request volume", "distinct sources", "asns", "traffic spike"),
    "Data Exfiltration": ("outbound", "dlp flagged", "uploaded to", "external cloud storage", "exported"),
    "Privilege Escalation": ("domain admins", "privilege escalation", "sudo", "system access", "elevated"),
    "Ransomware Indicator": ("ransomware", "shadow cop", "encryption", "renamed with a new extension"),
    "Suspicious Login": ("implausible travel", "new device/location", "mfa-approved", "active session", "successive logins"),
    "Web Application Attack": ("sql injection", "directory traversal", "injection payloads", "waf", "xss"),
    "C2 Beaconing": ("beacon", "dga", "newly-registered domain", "dns requests", "c2"),
}


class PlaceholderRetriever:
    name = "placeholder-keyword"

    def retrieve(self, alert: Alert, incidents: Sequence[Incident], k: int) -> list[IncidentMatch]:
        text = alert.description.lower()
        type_hits = {t: sum(cue in text for cue in cues) for t, cues in _PLACEHOLDER_CUES.items()}
        alert_words = set(re.findall(r"[a-z]{4,}", text))
        scored = []
        for inc in incidents:
            overlap = len(alert_words & set(re.findall(r"[a-z]{4,}", inc.circumstances.lower())))
            score = 0.8 * min(type_hits.get(inc.alert_type, 0) / 2, 1) + 0.2 * min(overlap / 4, 1)
            if type_hits.get(inc.alert_type, 0) == 0:
                score *= 0.3
            scored.append(IncidentMatch(incident=inc, score=round(min(score, 1.0), 3), method=self.name))
        scored.sort(key=lambda m: m.score, reverse=True)
        return [m for m in scored[:k] if m.score > 0]


_retriever: IncidentRetriever = PlaceholderRetriever()


def get_retriever() -> IncidentRetriever:
    return _retriever


def set_retriever(retriever: IncidentRetriever) -> None:
    global _retriever
    _retriever = retriever
