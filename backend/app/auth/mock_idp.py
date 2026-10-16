"""Standalone local identity provider used only when AUTH_PROVIDER=mock.

Mimics the pieces of an OIDC Authorization Code flow the backend's real
app/auth/oidc.py client needs (authorize -> code -> token -> claims), so
switching AUTH_PROVIDER=azuread later requires no change to that client
interface, only to which issuer it talks to.

Run as its own container: `uvicorn app.auth.mock_idp:app --port 8100`.
"""

import os
import time
import uuid

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from jose import jwt

from app.auth.demo_users import DEMO_USERS

CLIENT_ID = os.environ.get("OIDC_CLIENT_ID", "dhl-hosting-advisor")
CLIENT_SECRET = os.environ.get("OIDC_CLIENT_SECRET", "dev-secret")
SIGNING_KEY = os.environ.get("JWT_SIGNING_KEY", "dev-only-signing-key-change-me")
ALGORITHM = "HS256"
CODE_TTL_SECONDS = 120

app = FastAPI(title="DHL Hosting Advisor — Mock IdP")

_pending_codes: dict[str, dict] = {}  # code -> {user, redirect_uri, expires_at}


@app.get("/login", response_class=HTMLResponse)
def login_page(redirect_uri: str, state: str = ""):
    buttons = "\n".join(
        f'<form method="post" action="/login" style="margin-bottom:10px">'
        f'<input type="hidden" name="sub" value="{u["sub"]}">'
        f'<input type="hidden" name="redirect_uri" value="{redirect_uri}">'
        f'<input type="hidden" name="state" value="{state}">'
        f'<button type="submit" style="padding:10px 16px;width:100%;text-align:left;'
        f'border:1px solid #ccc;border-radius:6px;background:#fff;cursor:pointer">{u["label"]}</button>'
        f"</form>"
        for u in DEMO_USERS
    )
    return f"""
    <html><body style="font-family:sans-serif;max-width:480px;margin:60px auto">
    <h2>DHL Hosting Advisor — Mock sign-in</h2>
    <p style="color:#666">Local development identity provider. Pick a demo identity.</p>
    {buttons}
    </body></html>
    """


@app.post("/login")
def login_submit(sub: str = Form(...), redirect_uri: str = Form(...), state: str = Form("")):
    user = next((u for u in DEMO_USERS if u["sub"] == sub), None)
    if not user:
        raise HTTPException(404, "Unknown demo identity")
    code = uuid.uuid4().hex
    _pending_codes[code] = {"user": user, "expires_at": time.time() + CODE_TTL_SECONDS}
    separator = "&" if "?" in redirect_uri else "?"
    return RedirectResponse(f"{redirect_uri}{separator}code={code}&state={state}", status_code=303)


@app.post("/token")
def token(code: str = Form(...), client_id: str = Form(...), client_secret: str = Form(...)):
    if client_id != CLIENT_ID or client_secret != CLIENT_SECRET:
        raise HTTPException(401, "Invalid client credentials")
    entry = _pending_codes.pop(code, None)
    if not entry or entry["expires_at"] < time.time():
        raise HTTPException(400, "Invalid or expired code")
    user = entry["user"]
    claims = {
        "sub": user["sub"],
        "email": user["email"],
        "name": user["name"],
        "roles": user["roles"],
        "domain": user["domain"],
        "iss": "mock-idp",
        "aud": CLIENT_ID,
        "exp": int(time.time()) + 3600,
    }
    id_token = jwt.encode(claims, SIGNING_KEY, algorithm=ALGORITHM)
    return {"access_token": id_token, "id_token": id_token, "token_type": "bearer"}


@app.get("/health")
def health():
    return {"status": "ok"}
