"""Confidence score built from signals we can check.

The model's self-reported confidence is only 20% of the score; the rest comes from
retrieval strength, novelty, playbook ambiguity, data quality and evidence gaps.
Every deduction is listed so the analyst can see why the number is what it is.
"""

from pydantic import BaseModel

from . import config
from .models import IncidentMatch, Investigation, QualityFlag

NOVEL_PREFACE = "Based on what I've seen, this is my analysis:"


class Factor(BaseModel):
    factor: str
    delta: int
    detail: str


class Confidence(BaseModel):
    score: int
    band: str
    factors: list[Factor]
    novel: bool
    preface: str | None


def score(
    matches: list[IncidentMatch],
    secondary_playbook: bool,
    flags: list[QualityFlag],
    inv: Investigation,
) -> Confidence:
    factors: list[Factor] = []
    top = matches[0].score if matches else 0.0

    novel = top < config.NOVELTY_THRESHOLD or inv.is_novel
    if novel:
        factors.append(Factor(factor="novelty", delta=-30, detail=f"No close historical match (best {top:.2f}) - first time seeing this"))
    elif top < 0.5:
        factors.append(Factor(factor="weak_history", delta=-10, detail=f"Best historical match is only {top:.2f}"))

    if secondary_playbook:
        factors.append(Factor(factor="playbook_ambiguity", delta=-10, detail="Two playbooks scored close together"))

    quality_penalty = min(sum(f.penalty for f in flags), 40)
    if quality_penalty:
        codes = ", ".join(f.code for f in flags)
        factors.append(Factor(factor="data_quality", delta=-quality_penalty, detail=codes))

    gaps = sum(s.status == "evidence_unavailable" for s in inv.steps)
    if gaps:
        factors.append(Factor(factor="evidence_gaps", delta=-min(3 * gaps, 15), detail=f"{gaps} playbook step(s) lacked the data to check"))

    signal = max(0, 100 + sum(f.delta for f in factors))
    model_conf = max(0, min(inv.model_confidence, 100))
    final = round(0.8 * signal + 0.2 * model_conf)
    factors.append(Factor(factor="model_self_report", delta=final - signal, detail=f"Model said {model_conf}; weighted 20%"))

    band = "high" if final >= config.AUTO_CLOSE_CONFIDENCE else "medium" if final >= config.LOW_CONFIDENCE_THRESHOLD else "low"
    return Confidence(score=final, band=band, factors=factors, novel=novel, preface=NOVEL_PREFACE if novel else None)
