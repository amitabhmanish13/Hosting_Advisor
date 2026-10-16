from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.audit import log_action
from app.auth.deps import get_current_user, require_role
from app.auth.rbac import can_access_domain, visible_domain_ids
from app.db.models import (
    Assessment,
    AssessmentStatus,
    KnockoutAnswer,
    Role,
    ScoringAnswer,
    UserAccount,
    YesNo,
)
from app.db.models import Band as BandModel
from app.db.session import get_db
from app.engine.apply import recompute
from app.routers.questionnaires import get_current_published
from app.schemas import (
    AnswersIn,
    AssessmentCreateIn,
    AssessmentDetailOut,
    AssessmentListItemOut,
    AssessmentProfileIn,
    AssessmentResultOut,
    DriverSignalOut,
)

router = APIRouter(prefix="/assessments", tags=["assessments"])


def load_assessment(db: Session, assessment_id: int) -> Assessment:
    assessment = (
        db.query(Assessment)
        .options(
            selectinload(Assessment.domain),
            selectinload(Assessment.questionnaire_version),
            selectinload(Assessment.knockout_answers).selectinload(KnockoutAnswer.question),
            selectinload(Assessment.scoring_answers).selectinload(ScoringAnswer.question),
            selectinload(Assessment.result),
            selectinload(Assessment.workflow_events),
        )
        .filter_by(id=assessment_id)
        .first()
    )
    if not assessment:
        raise HTTPException(404, "Assessment not found")
    return assessment


def assert_visible(user: UserAccount, assessment: Assessment) -> None:
    scope = visible_domain_ids(user)
    if scope is not None and assessment.domain_id not in scope:
        raise HTTPException(403, "Not authorized to view this domain's assessments")


def build_detail(db: Session, assessment: Assessment) -> AssessmentDetailOut:
    result, engine_result = recompute(db, assessment)
    db.commit()
    db.refresh(assessment)

    base = AssessmentDetailOut.model_validate(assessment)
    for out, row in zip(base.knockout_answers, assessment.knockout_answers):
        q = row.question
        out.code, out.direction, out.dimension = q.code, q.direction.value, q.dimension
        out.question_text, out.evidence_hint = q.question_text, q.evidence_hint
    for out, row in zip(base.scoring_answers, assessment.scoring_answers):
        q = row.question
        out.code, out.dimension, out.question_text, out.evidence_hint = q.code, q.dimension, q.question_text, q.evidence_hint
        out.band_a_text, out.band_b_text = q.band_a_text, q.band_b_text
        out.band_c_text, out.band_d_text, out.band_e_text = q.band_c_text, q.band_d_text, q.band_e_text
    base.result = AssessmentResultOut(
        private_points=result.private_points,
        public_points=result.public_points,
        private_fit=result.private_fit,
        public_fit=result.public_fit,
        recommendation=result.recommendation,
        confidence=result.confidence.value,
        robust=result.robust,
        evidence_complete=result.evidence_complete,
        top_private_drivers=[DriverSignalOut(**vars(d)) for d in engine_result.top_private_drivers],
        top_public_drivers=[DriverSignalOut(**vars(d)) for d in engine_result.top_public_drivers],
    )
    return base


@router.post("", response_model=AssessmentDetailOut)
def create_assessment(
    payload: AssessmentCreateIn,
    db: Session = Depends(get_db),
    user: UserAccount = Depends(require_role(Role.assessor, Role.admin)),
):
    if not can_access_domain(user, Role.assessor, payload.domain_id) and not any(
        r.role == Role.admin for r in user.roles
    ):
        raise HTTPException(403, "Not authorized to create assessments for this domain")

    version = get_current_published(db)
    assessment = Assessment(
        questionnaire_version_id=version.id,
        status=AssessmentStatus.draft,
        created_by=user.id,
        **payload.model_dump(),
    )
    db.add(assessment)
    db.flush()
    for k in version.knockout_questions:
        db.add(KnockoutAnswer(assessment_id=assessment.id, knockout_question_id=k.id))
    for s in version.scoring_questions:
        db.add(ScoringAnswer(assessment_id=assessment.id, scoring_question_id=s.id))
    db.commit()

    log_action(db, user.id, "create", "assessment", assessment.id)
    db.commit()
    return build_detail(db, load_assessment(db, assessment.id))


@router.get("", response_model=list[AssessmentListItemOut])
def list_assessments(
    domain_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    user: UserAccount = Depends(get_current_user),
):
    query = db.query(Assessment).options(
        selectinload(Assessment.domain), selectinload(Assessment.questionnaire_version), selectinload(Assessment.result)
    )
    scope = visible_domain_ids(user)
    if scope is not None:
        query = query.filter(Assessment.domain_id.in_(scope) if scope else False)
    if domain_id:
        query = query.filter(Assessment.domain_id == domain_id)
    if status:
        query = query.filter(Assessment.status == AssessmentStatus(status))

    out = []
    for a in query.order_by(Assessment.created_at.desc()).all():
        item = AssessmentListItemOut.model_validate(a)
        item.questionnaire_version_label = a.questionnaire_version.version_label
        if a.result:
            item.recommendation = a.result.recommendation
            item.confidence = a.result.confidence.value
        out.append(item)
    return out


@router.get("/{assessment_id}", response_model=AssessmentDetailOut)
def get_assessment(assessment_id: int, db: Session = Depends(get_db), user: UserAccount = Depends(get_current_user)):
    assessment = load_assessment(db, assessment_id)
    assert_visible(user, assessment)
    return build_detail(db, assessment)


@router.put("/{assessment_id}/profile", response_model=AssessmentDetailOut)
def update_profile(
    assessment_id: int,
    payload: AssessmentProfileIn,
    db: Session = Depends(get_db),
    user: UserAccount = Depends(get_current_user),
):
    assessment = load_assessment(db, assessment_id)
    assert_visible(user, assessment)
    if assessment.status != AssessmentStatus.draft:
        raise HTTPException(400, "Only Draft assessments can be edited")
    for field, value in payload.model_dump().items():
        setattr(assessment, field, value)
    db.commit()
    return build_detail(db, load_assessment(db, assessment_id))


@router.put("/{assessment_id}/answers", response_model=AssessmentDetailOut)
def update_answers(
    assessment_id: int,
    payload: AnswersIn,
    db: Session = Depends(get_db),
    user: UserAccount = Depends(get_current_user),
):
    assessment = load_assessment(db, assessment_id)
    assert_visible(user, assessment)
    if assessment.status != AssessmentStatus.draft:
        raise HTTPException(400, "Only Draft assessments can be edited")

    ko_by_qid = {a.knockout_question_id: a for a in assessment.knockout_answers}
    for item in payload.knockout_answers:
        row = ko_by_qid.get(item.knockout_question_id)
        if not row:
            raise HTTPException(400, f"Unknown knockout_question_id {item.knockout_question_id}")
        row.answer = YesNo(item.answer) if item.answer else None
        row.evidence_reference = item.evidence_reference

    sc_by_qid = {a.scoring_question_id: a for a in assessment.scoring_answers}
    for item in payload.scoring_answers:
        row = sc_by_qid.get(item.scoring_question_id)
        if not row:
            raise HTTPException(400, f"Unknown scoring_question_id {item.scoring_question_id}")
        row.band = BandModel(item.band) if item.band else None
        row.evidence_reference = item.evidence_reference

    db.commit()
    return build_detail(db, load_assessment(db, assessment_id))
