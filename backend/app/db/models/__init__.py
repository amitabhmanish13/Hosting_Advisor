import enum
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class QuestionnaireStatus(str, enum.Enum):
    draft = "draft"
    published = "published"


class Direction(str, enum.Enum):
    private = "private"
    public = "public"


class YesNo(str, enum.Enum):
    yes = "yes"
    no = "no"


class Band(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


class Role(str, enum.Enum):
    admin = "admin"
    assessor = "assessor"
    approver = "approver"
    viewer = "viewer"


class AssessmentStatus(str, enum.Enum):
    draft = "draft"
    submitted = "submitted"
    endorsed = "endorsed"
    decided = "decided"


class Confidence(str, enum.Enum):
    high = "high"
    medium = "medium"
    low = "low"
    na = "n/a"


def _enum(e: type[enum.Enum], **kw):
    return Enum(e, values_callable=lambda x: [m.value for m in x], native_enum=False, **kw)


class QuestionnaireVersion(Base):
    __tablename__ = "questionnaire_version"

    id: Mapped[int] = mapped_column(primary_key=True)
    version_label: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    status: Mapped[QuestionnaireStatus] = mapped_column(_enum(QuestionnaireStatus), nullable=False)
    changelog: Mapped[str | None] = mapped_column(Text)
    published_by: Mapped[str | None] = mapped_column(String(255))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    knockout_questions: Mapped[list["KnockoutQuestion"]] = relationship(
        back_populates="version", order_by="KnockoutQuestion.order_index", cascade="all, delete-orphan"
    )
    scoring_questions: Mapped[list["ScoringQuestion"]] = relationship(
        back_populates="version", order_by="ScoringQuestion.order_index", cascade="all, delete-orphan"
    )


class KnockoutQuestion(Base):
    __tablename__ = "knockout_question"

    id: Mapped[int] = mapped_column(primary_key=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("questionnaire_version.id"), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    code: Mapped[str] = mapped_column(String(16), nullable=False)  # KO1..KO6
    direction: Mapped[Direction] = mapped_column(_enum(Direction), nullable=False)
    dimension: Mapped[str] = mapped_column(String(128), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_hint: Mapped[str | None] = mapped_column(Text)
    dhl_ref: Mapped[str | None] = mapped_column(String(64))

    version: Mapped[QuestionnaireVersion] = relationship(back_populates="knockout_questions")


class ScoringQuestion(Base):
    __tablename__ = "scoring_question"

    id: Mapped[int] = mapped_column(primary_key=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("questionnaire_version.id"), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    code: Mapped[str] = mapped_column(String(16), nullable=False)  # Q1..Q14
    dimension: Mapped[str] = mapped_column(String(128), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_hint: Mapped[str | None] = mapped_column(Text)
    band_a_text: Mapped[str] = mapped_column(Text, nullable=False)
    band_b_text: Mapped[str] = mapped_column(Text, nullable=False)
    band_c_text: Mapped[str] = mapped_column(Text, nullable=False)
    band_d_text: Mapped[str] = mapped_column(Text, nullable=False)
    band_e_text: Mapped[str] = mapped_column(Text, nullable=False)
    dhl_ref: Mapped[str | None] = mapped_column(String(64))

    version: Mapped[QuestionnaireVersion] = relationship(back_populates="scoring_questions")


class Domain(Base):
    __tablename__ = "domain"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)


class UserAccount(Base):
    __tablename__ = "user_account"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_subject: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain_id: Mapped[int | None] = mapped_column(ForeignKey("domain.id"))

    domain: Mapped[Domain | None] = relationship()
    roles: Mapped[list["UserRole"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserRole(Base):
    __tablename__ = "user_role"
    __table_args__ = (UniqueConstraint("user_id", "role", "domain_id", name="uq_user_role_domain"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"), nullable=False)
    role: Mapped[Role] = mapped_column(_enum(Role), nullable=False)
    domain_id: Mapped[int | None] = mapped_column(ForeignKey("domain.id"))

    user: Mapped[UserAccount] = relationship(back_populates="roles")
    domain: Mapped[Domain | None] = relationship()


class Assessment(Base):
    __tablename__ = "assessment"

    id: Mapped[int] = mapped_column(primary_key=True)
    questionnaire_version_id: Mapped[int] = mapped_column(
        ForeignKey("questionnaire_version.id"), nullable=False
    )
    domain_id: Mapped[int] = mapped_column(ForeignKey("domain.id"), nullable=False)

    app_name: Mapped[str] = mapped_column(String(255), nullable=False)
    business_owner: Mapped[str | None] = mapped_column(String(255))
    technical_owner: Mapped[str | None] = mapped_column(String(255))
    data_classification: Mapped[str | None] = mapped_column(String(128))
    business_criticality: Mapped[str | None] = mapped_column(String(128))
    current_hosting: Mapped[str | None] = mapped_column(String(128))
    target_go_live: Mapped[date | None] = mapped_column(Date)
    rto_rpo: Mapped[str | None] = mapped_column(String(255))

    status: Mapped[AssessmentStatus] = mapped_column(_enum(AssessmentStatus), nullable=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("user_account.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    questionnaire_version: Mapped[QuestionnaireVersion] = relationship()
    domain: Mapped[Domain] = relationship()
    knockout_answers: Mapped[list["KnockoutAnswer"]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan"
    )
    scoring_answers: Mapped[list["ScoringAnswer"]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan"
    )
    result: Mapped["AssessmentResult | None"] = relationship(
        back_populates="assessment", cascade="all, delete-orphan", uselist=False
    )
    workflow_events: Mapped[list["WorkflowEvent"]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan", order_by="WorkflowEvent.created_at"
    )


class KnockoutAnswer(Base):
    __tablename__ = "knockout_answer"
    __table_args__ = (UniqueConstraint("assessment_id", "knockout_question_id", name="uq_ko_answer"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessment.id"), nullable=False)
    knockout_question_id: Mapped[int] = mapped_column(ForeignKey("knockout_question.id"), nullable=False)
    answer: Mapped[YesNo | None] = mapped_column(_enum(YesNo))
    evidence_reference: Mapped[str | None] = mapped_column(String(512))

    assessment: Mapped[Assessment] = relationship(back_populates="knockout_answers")
    question: Mapped[KnockoutQuestion] = relationship()


class ScoringAnswer(Base):
    __tablename__ = "scoring_answer"
    __table_args__ = (UniqueConstraint("assessment_id", "scoring_question_id", name="uq_score_answer"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessment.id"), nullable=False)
    scoring_question_id: Mapped[int] = mapped_column(ForeignKey("scoring_question.id"), nullable=False)
    band: Mapped[Band | None] = mapped_column(_enum(Band))
    evidence_reference: Mapped[str | None] = mapped_column(String(512))

    assessment: Mapped[Assessment] = relationship(back_populates="scoring_answers")
    question: Mapped[ScoringQuestion] = relationship()


class AssessmentResult(Base):
    __tablename__ = "assessment_result"

    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessment.id"), primary_key=True)
    private_points: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    public_points: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    private_fit: Mapped[float | None] = mapped_column(Float)
    public_fit: Mapped[float | None] = mapped_column(Float)
    recommendation: Mapped[str] = mapped_column(String(255), nullable=False)
    confidence: Mapped[Confidence] = mapped_column(_enum(Confidence), nullable=False)
    robust: Mapped[bool | None] = mapped_column(Boolean)
    evidence_complete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    assessment: Mapped[Assessment] = relationship(back_populates="result")


class WorkflowEvent(Base):
    __tablename__ = "workflow_event"

    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessment.id"), nullable=False)
    from_status: Mapped[AssessmentStatus] = mapped_column(_enum(AssessmentStatus), nullable=False)
    to_status: Mapped[AssessmentStatus] = mapped_column(_enum(AssessmentStatus), nullable=False)
    actor_user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    assessment: Mapped[Assessment] = relationship(back_populates="workflow_events")
    actor: Mapped[UserAccount] = relationship()


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("user_account.id"))
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
