"""Provider-agnostic OIDC client. Branches once on settings.auth_provider;
callers (app/routers/auth.py) never know which provider is behind it.

Switching from the local mock to real Azure AD is a config change only
(AUTH_PROVIDER=azuread + AZURE_TENANT_ID/OIDC_CLIENT_ID/OIDC_CLIENT_SECRET),
not a code change.
"""

from urllib.parse import urlencode

import httpx
from jose import jwt

from app.config import settings

_jwks_cache: dict | None = None


async def _azuread_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is None:
        async with httpx.AsyncClient() as client:
            discovery = (await client.get(f"{settings.oidc_issuer}/v2.0/.well-known/openid-configuration")).json()
            _jwks_cache = (await client.get(discovery["jwks_uri"])).json()
    return _jwks_cache


def get_authorize_url(state: str) -> str:
    # Uses oidc_browser_issuer, not oidc_issuer: inside Docker Compose the
    # issuer the backend talks to server-to-server (http://mock-idp:8100)
    # isn't reachable from the user's browser, which needs the host-mapped
    # http://localhost:8100 instead. Real Azure AD is reachable at the same
    # URL from both, so the two settings are simply equal there.
    if settings.auth_provider == "mock":
        params = urlencode({"redirect_uri": settings.oidc_redirect_uri, "state": state})
        return f"{settings.oidc_browser_issuer}/login?{params}"

    params = urlencode(
        {
            "client_id": settings.oidc_client_id,
            "response_type": "code",
            "redirect_uri": settings.oidc_redirect_uri,
            "response_mode": "query",
            "scope": "openid profile email",
            "state": state,
        }
    )
    return f"{settings.oidc_browser_issuer}/oauth2/v2.0/authorize?{params}"


async def exchange_code_for_claims(code: str) -> dict:
    """Returns claims shaped {sub, email, name, roles: [...], domain: str|None}."""
    if settings.auth_provider == "mock":
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.oidc_issuer}/token",
                data={
                    "code": code,
                    "client_id": settings.oidc_client_id,
                    "client_secret": settings.oidc_client_secret,
                },
            )
            resp.raise_for_status()
            id_token = resp.json()["id_token"]
        return jwt.decode(
            id_token,
            settings.jwt_signing_key,
            algorithms=["HS256"],
            audience=settings.oidc_client_id,
        )

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.oidc_issuer}/oauth2/v2.0/token",
            data={
                "client_id": settings.oidc_client_id,
                "client_secret": settings.oidc_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.oidc_redirect_uri,
            },
        )
        resp.raise_for_status()
        id_token = resp.json()["id_token"]

    jwks = await _azuread_jwks()
    claims = jwt.decode(id_token, jwks, audience=settings.oidc_client_id)
    # Azure AD app roles land in the `roles` claim once configured on the app
    # registration manifest; there is no native "domain" claim, so until the
    # tenant maps ITS domains to a group/claim, domain-scoped roles must be
    # assigned to the JIT-provisioned user manually via the Admin > Users panel.
    return {
        "sub": claims.get("oid") or claims["sub"],
        "email": claims.get("email") or claims.get("preferred_username"),
        "name": claims.get("name"),
        "roles": claims.get("roles", []),
        "domain": None,
    }
