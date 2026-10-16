"""Regression suite proving the engine faithfully ports the workbook.

Covers the 7 scenarios listed on the workbook's own "Formula Audit" sheet
(blank, private KO, public KO, conflict, clear private, clear public,
near-tie), plus the real DGFF/FEC reference case from the feedback
consolidation workbook (73% Private / 27% Public, High confidence, Robust).
"""

from app.engine.scoring import Band, Direction, KnockoutAnswerInput, ScoringAnswerInput, compute_result
from app.seed.questionnaire_v1 import KNOCKOUTS, SCORING

ALL_KO_CODES = [k["code"] for k in KNOCKOUTS]
ALL_SCORING_CODES = [s["code"] for s in SCORING]
DIRECTION_BY_CODE = {k["code"]: Direction(k["direction"]) for k in KNOCKOUTS}


def make_knockouts(yes_codes: set[str] = frozenset(), answered: bool = True, evidence: bool = True):
    return [
        KnockoutAnswerInput(
            code=code,
            direction=DIRECTION_BY_CODE[code],
            answer=("yes" if code in yes_codes else "no") if answered else None,
            evidence_reference=("doc-ref" if (code not in yes_codes or evidence) else None),
        )
        for code in ALL_KO_CODES
    ]


def make_scoring(bands: dict[str, Band] | None = None, answered: bool = True, evidence: bool = True):
    bands = bands or {}
    return [
        ScoringAnswerInput(
            code=code,
            dimension=code,
            band=bands.get(code, Band.C) if answered else None,
            evidence_reference="doc-ref" if evidence else None,
        )
        for code in ALL_SCORING_CODES
    ]


def test_blank_is_pending():
    result = compute_result(make_knockouts(answered=False), make_scoring(answered=False))
    assert result.complete is False
    assert result.recommendation == "Pending — complete all answers on the Questionnaire tab"
    assert result.confidence == "n/a"


def test_private_knockout_overrides_scoring():
    result = compute_result(make_knockouts(yes_codes={"KO1"}), make_scoring({c: Band.E for c in ALL_SCORING_CODES}))
    assert result.private_knockout_active is True
    assert result.conflict is False
    assert result.recommendation == "Private Cloud / On-Prem"
    assert result.confidence == "high"


def test_public_knockout_overrides_scoring():
    result = compute_result(make_knockouts(yes_codes={"KO4"}), make_scoring({c: Band.A for c in ALL_SCORING_CODES}))
    assert result.public_knockout_active is True
    assert result.recommendation == "Public Cloud"
    assert result.confidence == "high"


def test_conflicting_knockouts_escalate():
    result = compute_result(make_knockouts(yes_codes={"KO1", "KO4"}), make_scoring())
    assert result.conflict is True
    assert result.recommendation == "Conflict — escalate to Hosting Advisory Group"
    assert result.confidence == "n/a"


def test_clear_private_scoring():
    result = compute_result(make_knockouts(), make_scoring({c: Band.A for c in ALL_SCORING_CODES}))
    assert result.recommendation == "Private Cloud / On-Prem"
    assert result.confidence == "high"
    assert result.robust is True
    assert result.private_fit == 1.0
    assert result.public_fit == 0.0


def test_clear_public_scoring():
    result = compute_result(make_knockouts(), make_scoring({c: Band.E for c in ALL_SCORING_CODES}))
    assert result.recommendation == "Public Cloud"
    assert result.confidence == "high"
    assert result.robust is True


def test_near_tie_requires_architecture_review():
    bands = {c: (Band.A if i % 2 == 0 else Band.E) for i, c in enumerate(ALL_SCORING_CODES)}
    result = compute_result(make_knockouts(), make_scoring(bands))
    assert result.recommendation == "Near-tie — architecture review required"
    assert result.confidence == "low"


def test_decisive_but_fragile_result_is_not_robust():
    # 14 questions * 4 pts = 56 total. 3 questions at Band B (3/1) + 11 at Band C (2/2)
    # gives a point gap of exactly 6 -> fit gap 10.7% (decisive, >10pp) but under the
    # 8-point robustness threshold, so a single answer could still flip it.
    bands = {c: Band.C for c in ALL_SCORING_CODES}
    for code in ALL_SCORING_CODES[:3]:
        bands[code] = Band.B
    result = compute_result(make_knockouts(), make_scoring(bands))
    assert abs(result.private_points - result.public_points) == 6
    assert result.confidence == "medium"
    assert result.robust is False


def test_evidence_gate_flags_missing_reference_on_yes_knockout():
    result = compute_result(make_knockouts(yes_codes={"KO1"}, evidence=False), make_scoring())
    assert result.evidence_complete is False


def test_fec_reference_case_matches_real_submission():
    """Reproduces the DGFF/FEC use case from Hosting_Checklist_Feedback_Consolidation_v6:
    73% Private / 27% Public, High confidence, Robust, no knock-out, no evidence gaps,
    with Q13/Q7/Q6 as the strongest Private drivers and Q4 the only Public-leaning signal.
    """
    bands = {
        "Q4": Band.E,
        "Q6": Band.A,
        "Q7": Band.A,
        "Q13": Band.A,
        "Q12": Band.C,
        # remaining 9 questions lean mildly Private (Band B) to reach 41/15 overall
        **{c: Band.B for c in ALL_SCORING_CODES if c not in {"Q4", "Q6", "Q7", "Q13", "Q12"}},
    }
    result = compute_result(make_knockouts(), make_scoring(bands))

    assert result.private_knockout_active is False
    assert result.public_knockout_active is False
    assert result.private_points == 41
    assert result.public_points == 15
    assert round(result.private_fit * 100) == 73
    assert round(result.public_fit * 100) == 27
    assert result.recommendation == "Private Cloud / On-Prem"
    assert result.confidence == "high"
    assert result.robust is True
    assert result.evidence_complete is True

    private_driver_codes = {d.code for d in result.top_private_drivers}
    assert private_driver_codes.issubset({"Q6", "Q7", "Q13"})
    assert {d.code for d in result.top_public_drivers} == {"Q4"}
