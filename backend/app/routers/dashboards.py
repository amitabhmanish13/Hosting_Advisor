from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, selectinload

from app.auth.deps import get_current_user
from app.auth.rbac import visible_domain_ids
from app.db.models import Assessment, AssessmentStatus, UserAccount
from app.db.session import get_db
from app.schemas import ByDomainRowOut, ConfidenceRobustnessOut, NeedsAttentionItemOut, PortfolioOut

router = APIRouter(prefix="/dashboards", tags=["dashboards"])

STALE_AFTER_DAYS = 14


def _visible_assessments(db: Session, user: UserAccount):
    query = db.query(Assessment).options(selectinload(Assessment.domain), selectinload(Assessment.result))
    scope = visible_domain_ids(user)
    if scope is not None:
        query = query.filter(Assessment.domain_id.in_(scope) if scope else False)
    return query.all()


@router.get("/portfolio", response_model=PortfolioOut)
def portfolio(db: Session = Depends(get_db), user: UserAccount = Depends(get_current_user)):
    rows = _visible_assessments(db, user)
    by_status: dict[str, int] = {}
    by_recommendation: dict[str, int] = {}
    for a in rows:
        by_status[a.status.value] = by_status.get(a.status.value, 0) + 1
        rec = a.result.recommendation if a.result else "Pending — complete all answers on the Questionnaire tab"
        by_recommendation[rec] = by_recommendation.get(rec, 0) + 1
    return PortfolioOut(total=len(rows), by_status=by_status, by_recommendation=by_recommendation)


@router.get("/by-domain", response_model=list[ByDomainRowOut])
def by_domain(db: Session = Depends(get_db), user: UserAccount = Depends(get_current_user)):
    rows = _visible_assessments(db, user)
    buckets: dict[str, ByDomainRowOut] = {}
    for a in rows:
        row = buckets.setdefault(
            a.domain.name, ByDomainRowOut(domain=a.domain.name, total=0, private_count=0, public_count=0, pending_or_other_count=0)
        )
        row.total += 1
        rec = a.result.recommendation if a.result else ""
        if rec == "Private Cloud / On-Prem":
            row.private_count += 1
        elif rec == "Public Cloud":
            row.public_count += 1
        else:
            row.pending_or_other_count += 1
    return sorted(buckets.values(), key=lambda r: r.domain)


@router.get("/confidence", response_model=ConfidenceRobustnessOut)
def confidence(db: Session = Depends(get_db), user: UserAccount = Depends(get_current_user)):
    rows = _visible_assessments(db, user)
    by_confidence: dict[str, int] = {}
    robust_count = fragile_count = unknown_count = 0
    for a in rows:
        if not a.result:
            continue
        by_confidence[a.result.confidence.value] = by_confidence.get(a.result.confidence.value, 0) + 1
        if a.result.robust is True:
            robust_count += 1
        elif a.result.robust is False:
            fragile_count += 1
        else:
            unknown_count += 1
    return ConfidenceRobustnessOut(
        by_confidence=by_confidence, robust_count=robust_count, fragile_count=fragile_count, unknown_count=unknown_count
    )


@router.get("/needs-attention", response_model=list[NeedsAttentionItemOut])
def needs_attention(db: Session = Depends(get_db), user: UserAccount = Depends(get_current_user)):
    rows = _visible_assessments(db, user)
    stale_cutoff = datetime.now(UTC) - timedelta(days=STALE_AFTER_DAYS)
    items: list[NeedsAttentionItemOut] = []
    for a in rows:
        if a.result and a.result.recommendation == "Near-tie — architecture review required":
            items.append(NeedsAttentionItemOut(assessment_id=a.id, app_name=a.app_name, domain=a.domain.name, status=a.status.value, issue="Near-tie — architecture review required"))
        if a.result and not a.result.evidence_complete:
            items.append(NeedsAttentionItemOut(assessment_id=a.id, app_name=a.app_name, domain=a.domain.name, status=a.status.value, issue="Evidence reference missing on one or more answered questions"))
        if a.status != AssessmentStatus.decided and a.created_at.replace(tzinfo=UTC) < stale_cutoff:
            items.append(NeedsAttentionItemOut(assessment_id=a.id, app_name=a.app_name, domain=a.domain.name, status=a.status.value, issue=f"Stuck in '{a.status.value}' for over {STALE_AFTER_DAYS} days"))
    return items
