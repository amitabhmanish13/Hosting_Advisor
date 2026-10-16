"""Bridges the ORM (Assessment + its answers) to the framework-free engine in
scoring.py, and upserts the recomputed AssessmentResult. Called after every
answer write so the stored result is never stale.
"""

from sqlalchemy.orm import Session

from app.db.models import Assessment, AssessmentResult
from app.engine.scoring import Band, Direction, EngineResult, KnockoutAnswerInput, ScoringAnswerInput, compute_result


def recompute(db: Session, assessment: Assessment) -> tuple[AssessmentResult, EngineResult]:
    # .value is intentionally not used here: for an ORM object still pending
    # in this same session (not yet round-tripped through a fresh SELECT),
    # attributes hold whatever raw value was assigned, which may be a plain
    # str rather than the enum member. Direction(x)/Band(x) accept either,
    # since these are str-subclassing enums.
    knockouts = [
        KnockoutAnswerInput(
            code=a.question.code,
            direction=Direction(a.question.direction),
            answer=a.answer if a.answer else None,
            evidence_reference=a.evidence_reference,
        )
        for a in assessment.knockout_answers
    ]
    scorings = [
        ScoringAnswerInput(
            code=a.question.code,
            dimension=a.question.dimension,
            band=Band(a.band) if a.band else None,
            evidence_reference=a.evidence_reference,
        )
        for a in assessment.scoring_answers
    ]
    engine_result = compute_result(knockouts, scorings)

    result = assessment.result
    if not result:
        result = AssessmentResult(assessment_id=assessment.id)
        db.add(result)

    result.private_points = engine_result.private_points
    result.public_points = engine_result.public_points
    result.private_fit = engine_result.private_fit
    result.public_fit = engine_result.public_fit
    result.recommendation = engine_result.recommendation
    result.confidence = engine_result.confidence
    result.robust = engine_result.robust
    result.evidence_complete = engine_result.evidence_complete
    return result, engine_result
