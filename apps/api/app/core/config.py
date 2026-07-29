from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    env: Literal["dev", "staging", "prod"] = "dev"
    database_url: str
    redis_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_ttl_s: int = 3600
    refresh_ttl_s: int = 2592000
    cors_origins: str = "*"
    cf_account_id: str = ""
    cf_stream_signing_key: str = ""
    cf_r2_bucket: str = ""
    apple_bundle_id: str = ""
    apple_key_id: str = ""
    apple_team_id: str = ""
    apple_private_key: str = ""
    google_service_account_json: str = ""
    revenuecat_webhook_secret: str = ""
    revenuecat_api_key: str = ""
    tmdb_api_key: str | None = None
    tmdb_access_token: str | None = None
    paystack_secret_key: str = ""
    paystack_webhook_secret: str = ""
    paystack_public_key: str = ""
    sentry_dsn: str | None = None
    app_api_base_url: str = "http://localhost:8000"
    secret_key: str = ""
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    otp_length: int = 6
    otp_ttl_seconds: int = 600
    resend_api_key: str = ""
    resend_email_from: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
