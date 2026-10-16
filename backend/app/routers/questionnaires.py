from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.audit import log_action
from app.auth.deps import get_current_user, require_role
from app.db.models import (
    Assessment,
    KnockoutQuestion,
    QuestionnaireStatus,
    QuestionnaireVersion,
    Role,
    ScoringQuestion,
    UserAccount,
)
from app.db.session import get_db
from app.schemas import PublishIn, QuestionnaireDraftIn, QuestionnaireSummaryOut, QuestionnaireVersionOut

router = APIRouter(prefix="/questionnaires", tags=["questionnaires"])


def _with_questions(query):
    return query.options(
        selectinload(QuestionnaireVersion.knockout_questions),
        selectinload(QuestionnaireVersion.scoring_questions),
    )


def get_current_published(db: Session) -> QuestionnaireVersion:
    version = _with_questions(
        db.query(QuestionnaireVersion).filter_by(status=QuestionnaireStatus.published)
    ).order_by(QuestionnaireVersion.published_at.desc()).first()
    if not version:
        raise HTTPException(500, "No published questionnaire version exists")
    return version


@router.get("/current", response_model=QuestionnaireVersionOut)
def read_current(db: Session = Depends(get_db), _user: UserAccount = Depends(get_current_user)):
    return get_current_published(db)


@router.get("", response_model=list[QuestionnaireSummaryOut])
def list_versions(db: Session = Depends(get_db), _user: UserAccount = Depends(require_role(Role.admin))):
    rows = db.query(QuestionnaireVersion).order_by(QuestionnaireVersion.id.desc()).all()
    counts = dict(
        db.query(Assessment.questionnaire_version_id, func.count(Assessment.id))
        .group_by(Assessment.questionnaire_version_id)
        .all()
    )
    out = []
    for v in rows:
        item = QuestionnaireSummaryOut.model_validate(v)
        item.assessment_count = counts.get(v.id, 0)
        out.append(item)
    return out


@router.get("/draft", response_model=QuestionnaireVersionOut)
def get_or_create_draft(db: Session = Depends(get_db), _user: UserAccount = Depends(require_role(Role.admin))):
    draft = _with_questions(db.query(QuestionnaireVersion)).filter_by(status=QuestionnaireStatus.draft).first()
    if draft:
        return draft

    current = get_current_published(db)
    draft = QuestionnaireVersion(
        version_label=f"{current.version_label}-draft",
        status=QuestionnaireStatus.draft,
    )
    db.add(draft)
    db.flush()
    for k in current.knockout_questions:
        db.add(
            KnockoutQuestion(
                version_id=draft.id,
                order_index=k.order_index,
                code=k.code,
                direction=k.direction,
                dimension=k.dimension,
                question_text=k.question_text,
                evidence_hint=k.evidence_hint,
                dhl_ref=k.dhl_ref,
            )
        )
    for s in current.scoring_questions:
        db.add(
            ScoringQuestion(
                version_id=draft.id,
                order_index=s.order_index,
                code=s.code,
                dimension=s.dimension,
                question_text=s.question_text,
                evidence_hint=s.evidence_hint,
                band_a_text=s.band_a_text,
                band_b_text=s.band_b_text,
                band_c_text=s.band_c_text,
                band_d_text=s.band_d_text,
                band_e_text=s.band_e_text,
                dhl_ref=s.dhl_ref,
            )
        )
    db.commit()
    return _with_questions(db.query(QuestionnaireVersion)).filter_by(id=draft.id).first()


@router.put("/draft", response_model=QuestionnaireVersionOut)
def update_draft(
    payload: QuestionnaireDraftIn,
    db: Session = Depends(get_db),
    user: UserAccount = Depends(require_role(Role.admin)),
):
    draft = db.query(QuestionnaireVersion).filter_by(status=QuestionnaireStatus.draft).first()
    if not draft:
        raise HTTPException(400, "No draft exists — call GET /questionnaires/draft first")

    db.query(KnockoutQuestion).filter_by(version_id=draft.id).delete()
    db.query(ScoringQuestion).filter_by(version_id=draft.id).delete()
    for i, k in enumerate(payload.knockout_questions):
        db.add(KnockoutQuestion(version_id=draft.id, order_index=i, **k.model_dump()))
    for i, s in enumerate(payload.scoring_questions):
        db.add(ScoringQuestion(version_id=draft.id, order_index=i, **s.model_dump()))
    log_action(db, user.id, "update_draft", "questionnaire_version", draft.id)
    db.commit()
    return _with_questions(db.query(QuestionnaireVersion)).filter_by(id=draft.id).first()


@router.post("/draft/publish", response_model=QuestionnaireVersionOut)
def publish_draft(
    payload: PublishIn,
    db: Session = Depends(get_db),
    user: UserAccount = Depends(require_role(Role.admin)),
):
    draft = db.query(QuestionnaireVersion).filter_by(status=QuestionnaireStatus.draft).first()
    if not draft:
        raise HTTPException(400, "No draft exists to publish")
    if not draft.knockout_questions or not draft.scoring_questions:
        raise HTTPException(400, "Draft must have at least one knock-out and one scoring question")

    from datetime import UTC, datetime

    draft.version_label = payload.version_label
    draft.changelog = payload.changelog
    draft.status = QuestionnaireStatus.published
    draft.published_by = user.email
    draft.published_at = datetime.now(UTC)
    log_action(db, user.id, "publish", "questionnaire_version", draft.id, detail=payload.changelog)
    db.commit()
    return _with_questions(db.query(QuestionnaireVersion)).filter_by(id=draft.id).first()


@router.get("/{version_id}", response_model=QuestionnaireVersionOut)
def read_version(version_id: int, db: Session = Depends(get_db), _user: UserAccount = Depends(require_role(Role.admin))):
    # Registered after /draft and /draft/publish: Starlette matches routes by
    # declaration order, and {version_id} would otherwise swallow "draft" as a
    # string before FastAPI's int validation rejects it with a 422.
    version = _with_questions(db.query(QuestionnaireVersion)).filter_by(id=version_id).first()
    if not version:
        raise HTTPException(404, "Version not found")
    return version
