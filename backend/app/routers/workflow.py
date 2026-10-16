from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.audit import log_action
from app.auth.deps import get_current_user, require_role
from app.auth.rbac import can_access_domain
from app.db.models import AssessmentStatus, Role, UserAccount, WorkflowEvent
from app.db.session import get_db
from app.engine.apply import recompute
from app.routers.assessments import assert_visible, build_detail, load_assessment
from app.schemas import AssessmentDetailOut, WorkflowActionIn

router = APIRouter(prefix="/assessments", tags=["workflow"])


def _transition(db: Session, assessment_id: int, user: UserAccount, expected: AssessmentStatus, to: AssessmentStatus, notes: str | None):
    assessment = load_assessment(db, assessment_id)
    assert_visible(user, assessment)
    if assessment.status != expected:
        raise HTTPException(400, f"Assessment must be '{expected.value}' for this action, currently '{assessment.status.value}'")

    db.add(
        WorkflowEvent(
            assessment_id=assessment.id,
            from_status=assessment.status,
            to_status=to,
            actor_user_id=user.id,
            notes=notes,
        )
    )
    assessment.status = to
    log_action(db, user.id, f"workflow:{expected.value}->{to.value}", "assessment", assessment.id, detail=notes)
    db.commit()
    return build_detail(db, load_assessment(db, assessment_id))


@router.post("/{assessment_id}/workflow/submit", response_model=AssessmentDetailOut)
def submit(
    assessment_id: int,
    payload: WorkflowActionIn,
    db: Session = Depends(get_db),
    user: UserAccount = Depends(require_role(Role.assessor, Role.admin)),
):
    assessment = load_assessment(db, assessment_id)
    if not can_access_domain(user, Role.assessor, assessment.domain_id) and not any(r.role == Role.admin for r in user.roles):
        raise HTTPException(403, "Not authorized to submit for this domain")
    _, engine_result = recompute(db, assessment)
    if not engine_result.complete:
        raise HTTPException(400, "Cannot submit: not all knock-out and scoring questions are answered")
    db.commit()
    return _transition(db, assessment_id, user, AssessmentStatus.draft, AssessmentStatus.submitted, payload.notes)


@router.post("/{assessment_id}/workflow/endorse", response_model=AssessmentDetailOut)
def endorse(
    assessment_id: int,
    payload: WorkflowActionIn,
    db: Session = Depends(get_db),
    user: UserAccount = Depends(require_role(Role.approver, Role.admin)),
):
    return _transition(db, assessment_id, user, AssessmentStatus.submitted, AssessmentStatus.endorsed, payload.notes)


@router.post("/{assessment_id}/workflow/decide", response_model=AssessmentDetailOut)
def decide(
    assessment_id: int,
    payload: WorkflowActionIn,
    db: Session = Depends(get_db),
    user: UserAccount = Depends(require_role(Role.approver, Role.admin)),
):
    return _transition(db, assessment_id, user, AssessmentStatus.endorsed, AssessmentStatus.decided, payload.notes)
