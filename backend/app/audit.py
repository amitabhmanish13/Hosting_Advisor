from sqlalchemy.orm import Session

from app.db.models import AuditLog


def log_action(db: Session, actor_user_id: int | None, action: str, entity_type: str, entity_id: str, detail: str | None = None) -> None:
    db.add(
        AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            detail=detail,
        )
    )
