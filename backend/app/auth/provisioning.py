from sqlalchemy.orm import Session

from app.db.models import Domain, Role, UserAccount, UserRole


def provision_user(db: Session, claims: dict) -> UserAccount:
    """JIT-provisions a UserAccount (+ domain, + role grants) from OIDC claims.
    Shared by the real login callback and the seed script, so seeded demo
    users and first-time real logins behave identically.
    """
    domain = None
    if claims.get("domain"):
        domain = db.query(Domain).filter_by(name=claims["domain"]).first()
        if not domain:
            domain = Domain(name=claims["domain"])
            db.add(domain)
            db.flush()

    user = db.query(UserAccount).filter_by(external_subject=claims["sub"]).first()
    if not user:
        user = UserAccount(
            external_subject=claims["sub"],
            email=claims["email"],
            display_name=claims.get("name") or claims["email"],
            domain_id=domain.id if domain else None,
        )
        db.add(user)
        db.flush()

    existing_roles = {(r.role, r.domain_id) for r in user.roles}
    for role_name in claims.get("roles", []):
        role = Role(role_name)
        domain_id = domain.id if (domain and role == Role.assessor) else None
        if (role, domain_id) not in existing_roles:
            db.add(UserRole(user_id=user.id, role=role, domain_id=domain_id))

    return user
