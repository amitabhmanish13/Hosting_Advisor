from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.auth.session import read_session_token
from app.config import settings
from app.db.models import Role, UserAccount
from app.db.session import get_db


def get_current_user(request: Request, db: Session = Depends(get_db)) -> UserAccount:
    token = request.cookies.get(settings.session_cookie_name)
    user_id = read_session_token(token) if token else None
    if not user_id:
        raise HTTPException(401, "Not authenticated")
    user = db.get(UserAccount, user_id)
    if not user:
        raise HTTPException(401, "Session no longer valid")
    return user


def require_role(*allowed: Role):
    def _dep(user: UserAccount = Depends(get_current_user)) -> UserAccount:
        if not any(r.role in allowed for r in user.roles):
            raise HTTPException(403, f"Requires one of roles: {', '.join(allowed)}")
        return user

    return _dep
