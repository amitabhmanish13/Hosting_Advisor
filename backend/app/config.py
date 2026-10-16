from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://dhl:dhl@postgres:5432/dhl_hosting_advisor"

    auth_provider: str = "mock"  # "mock" | "azuread"
    oidc_issuer: str = "http://mock-idp:8100"  # server-to-server: token exchange + JWKS discovery
    oidc_browser_issuer: str = "http://localhost:8100"  # browser-facing: authorize/login redirect
    oidc_client_id: str = "dhl-hosting-advisor"
    oidc_client_secret: str = "dev-secret"
    oidc_redirect_uri: str = "http://localhost:3000/auth/callback"
    jwt_signing_key: str = "dev-only-signing-key-change-me"
    jwt_algorithm: str = "HS256"

    session_cookie_name: str = "dha_session"

    ipp_base_url: str = "http://localhost:4000"

    cors_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
