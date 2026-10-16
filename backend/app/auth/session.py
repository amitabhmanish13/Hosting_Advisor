import time

from jose import JWTError, jwt

from app.config import settings

SESSION_TTL_SECONDS = 7 * 24 * 3600


def create_session_token(user_id: int) -> str:
    claims = {"user_id": user_id, "exp": int(time.time()) + SESSION_TTL_SECONDS}
    return jwt.encode(claims, settings.jwt_signing_key, algorithm=settings.jwt_algorithm)


def read_session_token(token: str) -> int | None:
    try:
        claims = jwt.decode(token, settings.jwt_signing_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
    return claims.get("user_id")
