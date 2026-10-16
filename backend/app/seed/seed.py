"""Idempotent startup seed: domains, demo users, the live questionnaire v1.0,
and two example assessments (the real DGFF/FEC reference case and one
synthetic Public Cloud example) so dashboards aren't empty on first run.

Safe to call on every backend startup — it no-ops once a questionnaire
version already exists.
"""

from datetime import UTC, date, datetime

from sqlalchemy.orm import Session

from app.auth.demo_users import DEMO_USERS, DOMAINS
from app.auth.provisioning import provision_user
from app.db.models import (
    Assessment,
    AssessmentStatus,
    Domain,
    KnockoutAnswer,
    KnockoutQuestion,
    QuestionnaireStatus,
    QuestionnaireVersion,
    ScoringAnswer,
    ScoringQuestion,
    UserAccount,
    WorkflowEvent,
)
from app.engine.apply import recompute
from app.seed.questionnaire_v1 import KNOCKOUTS, SCORING

FEC_KNOCKOUT_ANSWERS = {code: ("no", "N/A — no binding mandate identified") for code in (k["code"] for k in KNOCKOUTS)}

FEC_SCORING_ANSWERS = {
    "Q1": ("A", "90-day telemetry — flat demand pattern"),
    "Q2": ("B", "12-month utilization telemetry"),
    "Q3": ("B", "Measured latency to on-prem dependencies"),
    "Q4": ("E", "Data-flow analysis — notable egress volume"),
    "Q5": ("A", "Approved 3-year TCO model"),
    "Q6": ("A", "FEC Architecture Diagram"),
    "Q7": ("A", "Release Calendar"),
    "Q8": ("C", "Data classification record / GDPR assessment"),
    "Q9": ("B", "Business rollout plan"),
    "Q10": ("B", "Application assessment"),
    "Q11": ("B", "Oracle Licensing Assessment"),
    "Q12": ("C", "Backup / DR documentation"),
    "Q13": ("A", "Monitoring coverage documentation"),
    "Q14": ("C", "Architecture Design Document"),
}

DEMO_APP_SCORING_ANSWERS = {
    "Q1": ("E", "Architecture sizing estimate — bursty greenfield load"),
    "Q2": ("E", "No production history yet — short committed lifespan"),
    "Q3": ("E", "No immovable on-prem dependency"),
    "Q4": ("E", None),  # deliberately missing evidence -> needs-attention demo
    "Q5": ("D", "Approved TCO model, public 5-15% lower"),
    "Q6": ("E", "Architecture designed around managed cloud services"),
    "Q7": ("E", "Same-day ephemeral environments via IaC"),
    "Q8": ("E", "Public / non-sensitive data"),
    "Q9": ("E", "Global user base expected within 12 months"),
    "Q10": ("E", "Already cloud-native"),
    "Q11": ("E", "Subscription / marketplace licensing only"),
    "Q12": ("D", "RTO/RPO achievable in cloud at lower cost"),
    "Q13": ("E", "No private landing zone planned for this class"),
    "Q14": ("D", "Fully portable container-based design"),
}


def seed_if_empty(db: Session) -> None:
    if db.query(QuestionnaireVersion).first():
        return

    for name in DOMAINS:
        db.add(Domain(name=name))
    db.flush()

    users_by_sub: dict[str, UserAccount] = {}
    for demo in DEMO_USERS:
        user = provision_user(db, demo)
        users_by_sub[demo["sub"]] = user
    db.flush()

    version = QuestionnaireVersion(
        version_label="v1.0",
        status=QuestionnaireStatus.published,
        changelog="Initial published version, transcribed from DHL_Hosting_Decision_Questionnaire_v1.0.",
        published_by="system-seed",
        published_at=datetime.now(UTC),
    )
    db.add(version)
    db.flush()

    ko_rows: dict[str, KnockoutQuestion] = {}
    for i, k in enumerate(KNOCKOUTS):
        row = KnockoutQuestion(version_id=version.id, order_index=i, **k)
        db.add(row)
        ko_rows[k["code"]] = row

    sc_rows: dict[str, ScoringQuestion] = {}
    for i, s in enumerate(SCORING):
        row = ScoringQuestion(version_id=version.id, order_index=i, **s)
        db.add(row)
        sc_rows[s["code"]] = row
    db.flush()

    dgff_domain = db.query(Domain).filter_by(name="DGFF / FEC").first()
    digital_domain = db.query(Domain).filter_by(name="Digital Solutions").first()
    dana = users_by_sub["mock|assessor-dgff"]
    priya = users_by_sub["mock|assessor-digital"]
    jordan = users_by_sub["mock|approver"]

    fec = Assessment(
        questionnaire_version_id=version.id,
        domain_id=dgff_domain.id,
        app_name="FEC - Freight Event Capture",
        technical_owner="Jaromir Sindlar",
        data_classification="For Internal Use",
        business_criticality="High",
        current_hosting="ITS Private Cloud",
        target_go_live=date(2026, 8, 4),
        rto_rpo=None,
        status=AssessmentStatus.decided,
        created_by=dana.id,
    )
    db.add(fec)
    db.flush()
    _answer(db, fec, ko_rows, sc_rows, FEC_KNOCKOUT_ANSWERS, FEC_SCORING_ANSWERS)
    recompute(db, fec)
    db.add(WorkflowEvent(assessment_id=fec.id, from_status=AssessmentStatus.draft, to_status=AssessmentStatus.submitted, actor_user_id=dana.id, notes="Submitted for Hosting Advisory Group review."))
    db.add(WorkflowEvent(assessment_id=fec.id, from_status=AssessmentStatus.submitted, to_status=AssessmentStatus.endorsed, actor_user_id=jordan.id, notes="Endorsed — evidence-based score, high confidence, robust."))
    db.add(WorkflowEvent(assessment_id=fec.id, from_status=AssessmentStatus.endorsed, to_status=AssessmentStatus.decided, actor_user_id=jordan.id, notes="Management Board decision: Private Cloud / On-Prem confirmed."))

    demo_app = Assessment(
        questionnaire_version_id=version.id,
        domain_id=digital_domain.id,
        app_name="Greenfield Customer Portal (demo)",
        technical_owner="Demo Architect",
        data_classification="Public / non-sensitive",
        business_criticality="Medium",
        current_hosting="Not yet hosted — greenfield",
        target_go_live=date(2027, 1, 15),
        rto_rpo="RTO < 4h / RPO < 15min",
        status=AssessmentStatus.submitted,
        created_by=priya.id,
    )
    db.add(demo_app)
    db.flush()
    _answer(db, demo_app, ko_rows, sc_rows, {code: ("no", "N/A") for code in ko_rows}, DEMO_APP_SCORING_ANSWERS)
    recompute(db, demo_app)
    db.add(WorkflowEvent(assessment_id=demo_app.id, from_status=AssessmentStatus.draft, to_status=AssessmentStatus.submitted, actor_user_id=priya.id, notes="Submitted — awaiting Hosting Advisory Group endorsement."))

    db.commit()


def _answer(db, assessment, ko_rows, sc_rows, ko_answers, sc_answers):
    for code, (answer, evidence) in ko_answers.items():
        db.add(KnockoutAnswer(assessment_id=assessment.id, knockout_question_id=ko_rows[code].id, answer=answer, evidence_reference=evidence))
    for code, (band, evidence) in sc_answers.items():
        db.add(ScoringAnswer(assessment_id=assessment.id, scoring_question_id=sc_rows[code].id, band=band, evidence_reference=evidence))
    db.flush()
