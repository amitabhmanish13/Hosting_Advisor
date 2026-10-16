from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

# ---------- Questionnaire ----------


class KnockoutQuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_index: int
    code: str
    direction: str
    dimension: str
    question_text: str
    evidence_hint: str | None
    dhl_ref: str | None


class ScoringQuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_index: int
    code: str
    dimension: str
    question_text: str
    evidence_hint: str | None
    band_a_text: str
    band_b_text: str
    band_c_text: str
    band_d_text: str
    band_e_text: str
    dhl_ref: str | None


class QuestionnaireVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    version_label: str
    status: str
    changelog: str | None
    published_by: str | None
    published_at: datetime | None
    knockout_questions: list[KnockoutQuestionOut]
    scoring_questions: list[ScoringQuestionOut]


class QuestionnaireSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    version_label: str
    status: str
    changelog: str | None
    published_at: datetime | None
    assessment_count: int = 0


class KnockoutQuestionIn(BaseModel):
    code: str
    direction: str
    dimension: str
    question_text: str
    evidence_hint: str | None = None
    dhl_ref: str | None = None


class ScoringQuestionIn(BaseModel):
    code: str
    dimension: str
    question_text: str
    evidence_hint: str | None = None
    band_a_text: str
    band_b_text: str
    band_c_text: str
    band_d_text: str
    band_e_text: str
    dhl_ref: str | None = None


class QuestionnaireDraftIn(BaseModel):
    knockout_questions: list[KnockoutQuestionIn]
    scoring_questions: list[ScoringQuestionIn]


class PublishIn(BaseModel):
    version_label: str
    changelog: str


# ---------- Domains & Users ----------


class DomainOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class DomainIn(BaseModel):
    name: str


class UserRoleOut(BaseModel):
    role: str
    domain_id: int | None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    display_name: str
    domain: DomainOut | None
    roles: list[UserRoleOut]


class UserRoleIn(BaseModel):
    role: str
    domain_id: int | None = None


# ---------- Assessments ----------


class AssessmentCreateIn(BaseModel):
    app_name: str
    domain_id: int
    business_owner: str | None = None
    technical_owner: str | None = None
    data_classification: str | None = None
    business_criticality: str | None = None
    current_hosting: str | None = None
    target_go_live: date | None = None
    rto_rpo: str | None = None


class AssessmentProfileIn(AssessmentCreateIn):
    pass


class KnockoutAnswerIn(BaseModel):
    knockout_question_id: int
    answer: str | None = None  # "yes" | "no"
    evidence_reference: str | None = None


class ScoringAnswerIn(BaseModel):
    scoring_question_id: int
    band: str | None = None  # "A".."E"
    evidence_reference: str | None = None


class AnswersIn(BaseModel):
    knockout_answers: list[KnockoutAnswerIn] = []
    scoring_answers: list[ScoringAnswerIn] = []


class KnockoutAnswerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    knockout_question_id: int
    code: str = ""
    direction: str = ""
    dimension: str = ""
    question_text: str = ""
    evidence_hint: str | None = None
    answer: str | None
    evidence_reference: str | None


class ScoringAnswerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    scoring_question_id: int
    code: str = ""
    dimension: str = ""
    question_text: str = ""
    evidence_hint: str | None = None
    band_a_text: str = ""
    band_b_text: str = ""
    band_c_text: str = ""
    band_d_text: str = ""
    band_e_text: str = ""
    band: str | None
    evidence_reference: str | None


class DriverSignalOut(BaseModel):
    code: str
    dimension: str
    net_private_points: float


class AssessmentResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    private_points: float
    public_points: float
    private_fit: float | None
    public_fit: float | None
    recommendation: str
    confidence: str
    robust: bool | None
    evidence_complete: bool
    top_private_drivers: list[DriverSignalOut] = []
    top_public_drivers: list[DriverSignalOut] = []


class WorkflowEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    from_status: str
    to_status: str
    actor_user_id: int
    notes: str | None
    created_at: datetime


class AssessmentListItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    app_name: str
    domain: DomainOut
    status: str
    questionnaire_version_label: str = ""
    created_at: datetime
    recommendation: str | None = None
    confidence: str | None = None


class AssessmentDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    app_name: str
    domain: DomainOut
    status: str
    business_owner: str | None
    technical_owner: str | None
    data_classification: str | None
    business_criticality: str | None
    current_hosting: str | None
    target_go_live: date | None
    rto_rpo: str | None
    created_at: datetime
    questionnaire_version: QuestionnaireVersionOut
    knockout_answers: list[KnockoutAnswerOut]
    scoring_answers: list[ScoringAnswerOut]
    result: AssessmentResultOut | None
    workflow_events: list[WorkflowEventOut]


class WorkflowActionIn(BaseModel):
    notes: str | None = None


class HandoffOut(BaseModel):
    url: str
    app_name: str
    recommended_target: str
    assessment_id: int


# ---------- Dashboards ----------


class PortfolioOut(BaseModel):
    total: int
    by_status: dict[str, int]
    by_recommendation: dict[str, int]


class ByDomainRowOut(BaseModel):
    domain: str
    total: int
    private_count: int
    public_count: int
    pending_or_other_count: int


class ConfidenceRobustnessOut(BaseModel):
    by_confidence: dict[str, int]
    robust_count: int
    fragile_count: int
    unknown_count: int


class NeedsAttentionItemOut(BaseModel):
    assessment_id: int
    app_name: str
    domain: str
    status: str
    issue: str
