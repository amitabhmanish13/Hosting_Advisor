"""Pure port of the DHL Hosting Decision Questionnaire v1.0 scoring/decision rules.

No DB or framework imports here — this module is unit-tested directly against
the workbook's own "Formula Audit" scenarios and the real FEC reference case.
"""

from dataclasses import dataclass
from enum import Enum

NEAR_TIE_THRESHOLD = 0.10
ROBUSTNESS_POINT_GAP = 8
HIGH_CONFIDENCE_GAP = 0.30


class Direction(str, Enum):
    private = "private"
    public = "public"


class Band(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


BAND_POINTS: dict[Band, tuple[int, int]] = {
    Band.A: (4, 0),
    Band.B: (3, 1),
    Band.C: (2, 2),
    Band.D: (1, 3),
    Band.E: (0, 4),
}


@dataclass
class KnockoutAnswerInput:
    code: str
    direction: Direction
    answer: str | None  # "yes" | "no" | None
    evidence_reference: str | None


@dataclass
class ScoringAnswerInput:
    code: str
    dimension: str
    band: Band | None
    evidence_reference: str | None


@dataclass
class DriverSignal:
    code: str
    dimension: str
    net_private_points: float  # positive => private-leaning, negative => public-leaning


@dataclass
class EngineResult:
    complete: bool
    private_knockout_active: bool
    public_knockout_active: bool
    conflict: bool
    private_points: float
    public_points: float
    private_fit: float | None
    public_fit: float | None
    recommendation: str
    confidence: str  # "high" | "medium" | "low" | "n/a"
    robust: bool | None
    evidence_complete: bool
    top_private_drivers: list[DriverSignal]
    top_public_drivers: list[DriverSignal]


def compute_result(
    knockouts: list[KnockoutAnswerInput],
    scorings: list[ScoringAnswerInput],
) -> EngineResult:
    answered_ko = [k for k in knockouts if k.answer is not None]
    answered_sc = [s for s in scorings if s.band is not None]
    complete = (
        len(knockouts) > 0
        and len(scorings) > 0
        and len(answered_ko) == len(knockouts)
        and len(answered_sc) == len(scorings)
    )

    private_points = sum(BAND_POINTS[s.band][0] for s in answered_sc)
    public_points = sum(BAND_POINTS[s.band][1] for s in answered_sc)
    total_awarded = private_points + public_points
    private_fit = private_points / total_awarded if total_awarded else None
    public_fit = public_points / total_awarded if total_awarded else None

    private_active = any(k.answer == "yes" and k.direction == Direction.private for k in knockouts)
    public_active = any(k.answer == "yes" and k.direction == Direction.public for k in knockouts)
    conflict = private_active and public_active

    drivers = [
        DriverSignal(
            code=s.code,
            dimension=s.dimension,
            net_private_points=BAND_POINTS[s.band][0] - BAND_POINTS[s.band][1],
        )
        for s in answered_sc
    ]
    top_private = sorted((d for d in drivers if d.net_private_points >= 1), key=lambda d: -d.net_private_points)[:2]
    top_public = sorted((d for d in drivers if d.net_private_points <= -1), key=lambda d: d.net_private_points)[:2]

    robust = abs(private_points - public_points) > ROBUSTNESS_POINT_GAP if answered_sc and len(answered_sc) == len(scorings) else None
    evidence_complete = not any(
        k.answer == "yes" and not k.evidence_reference for k in knockouts
    ) and not any(s.band is not None and not s.evidence_reference for s in scorings)

    if not complete:
        recommendation = "Pending — complete all answers on the Questionnaire tab"
        confidence = "n/a"
    elif conflict:
        recommendation = "Conflict — escalate to Hosting Advisory Group"
        confidence = "n/a"
    elif private_active:
        recommendation = "Private Cloud / On-Prem"
        confidence = "high"
    elif public_active:
        recommendation = "Public Cloud"
        confidence = "high"
    else:
        gap = (private_fit or 0) - (public_fit or 0)
        gap_abs = abs(gap)
        if gap_abs < NEAR_TIE_THRESHOLD:
            recommendation = "Near-tie — architecture review required"
            confidence = "low"
        else:
            recommendation = "Private Cloud / On-Prem" if gap > 0 else "Public Cloud"
            confidence = "high" if gap_abs >= HIGH_CONFIDENCE_GAP else "medium"

    return EngineResult(
        complete=complete,
        private_knockout_active=private_active,
        public_knockout_active=public_active,
        conflict=conflict,
        private_points=private_points,
        public_points=public_points,
        private_fit=private_fit,
        public_fit=public_fit,
        recommendation=recommendation,
        confidence=confidence,
        robust=robust,
        evidence_complete=evidence_complete,
        top_private_drivers=top_private,
        top_public_drivers=top_public,
    )
