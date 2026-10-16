import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.auth.oidc import exchange_code_for_claims, get_authorize_url
from app.auth.provisioning import provision_user
from app.auth.session import create_session_token
from app.config import settings
from app.db.models import UserAccount
from app.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

STATE_COOKIE = "dha_oauth_state"


@router.get("/login")
def login(request: Request):
    state = uuid.uuid4().hex
    response = RedirectResponse(get_authorize_url(state))
    response.set_cookie(STATE_COOKIE, state, httponly=True, max_age=300, samesite="lax")
    return response


@router.get("/callback")
async def callback(request: Request, code: str, state: str, db: Session = Depends(get_db)):
    expected_state = request.cookies.get(STATE_COOKIE)
    if not expected_state or expected_state != state:
        raise HTTPException(400, "Invalid OAuth state")

    claims = await exchange_code_for_claims(code)
    user = provision_user(db, claims)
    db.commit()

    token = create_session_token(user.id)
    response = RedirectResponse("http://localhost:3000/")
    response.set_cookie(
        settings.session_cookie_name, token, httponly=True, max_age=7 * 24 * 3600, samesite="lax"
    )
    response.delete_cookie(STATE_COOKIE)
    return response


@router.get("/me")
def me(user: UserAccount = Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "domain": user.domain.name if user.domain else None,
        "roles": [{"role": r.role.value, "domain_id": r.domain_id} for r in user.roles],
    }


@router.post("/logout")
def logout():
    # Called via fetch from the SPA, not a top-level navigation: a redirect
    # response here fails the browser's CORS check on the redirected hop
    # (that final response has no CORS headers), so this returns plain JSON
    # and the frontend navigates itself after the cookie is cleared.
    response = JSONResponse({"status": "signed_out"})
    response.delete_cookie(settings.session_cookie_name)
    return response
