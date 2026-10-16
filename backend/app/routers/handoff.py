from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.config import settings
from app.db.models import AssessmentStatus, UserAccount
from app.db.session import get_db
from app.routers.assessments import assert_visible, load_assessment
from app.schemas import HandoffOut

router = APIRouter(prefix="/assessments", tags=["handoff"])

RECOMMENDATION_TO_TARGET = {
    "Private Cloud / On-Prem": "private",
    "Public Cloud": "public",
}


@router.get("/{assessment_id}/handoff", response_model=HandoffOut)
def handoff(assessment_id: int, db: Session = Depends(get_db), user: UserAccount = Depends(get_current_user)):
    assessment = load_assessment(db, assessment_id)
    assert_visible(user, assessment)
    if assessment.status != AssessmentStatus.decided:
        raise HTTPException(400, "Handoff is only available once the assessment is Decided")
    if not assessment.result or assessment.result.recommendation not in RECOMMENDATION_TO_TARGET:
        raise HTTPException(400, "Handoff requires a clear Private/Public recommendation (no conflict or near-tie)")

    target = RECOMMENDATION_TO_TARGET[assessment.result.recommendation]
    query = urlencode(
        {
            "app": assessment.app_name,
            "target": target,
            "source": "hosting-advisor",
            "assessmentId": assessment.id,
        }
    )
    return HandoffOut(
        url=f"{settings.ipp_base_url}/provision/new?{query}",
        app_name=assessment.app_name,
        recommended_target=target,
        assessment_id=assessment.id,
    )
