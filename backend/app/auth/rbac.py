"""Domain-scoping helpers shared by routers. A role grant with domain_id=None
is global (sees/acts on every domain); a grant with a domain_id scopes that
role to just that domain. A user can hold the same role with multiple grants.
"""

from app.db.models import Role, UserAccount


def has_global_grant(user: UserAccount, role: Role) -> bool:
    return any(r.role == role and r.domain_id is None for r in user.roles)


def scoped_domain_ids(user: UserAccount, role: Role) -> set[int] | None:
    """None means global scope for this role. Empty set means the user holds
    no grant of this role at all."""
    if has_global_grant(user, role):
        return None
    return {r.domain_id for r in user.roles if r.role == role and r.domain_id is not None}


def can_access_domain(user: UserAccount, role: Role, domain_id: int) -> bool:
    scope = scoped_domain_ids(user, role)
    return scope is None or domain_id in scope


def visible_domain_ids(user: UserAccount) -> set[int] | None:
    """Broadest read scope across all of a user's role grants. None means the
    user can see every domain (holds at least one global grant)."""
    if any(r.domain_id is None for r in user.roles):
        return None
    return {r.domain_id for r in user.roles if r.domain_id is not None}
