from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = Field(default="development")
    database_url: str
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str
    jwt_alg: str = "HS256"
    jwt_expires_hours: int = 720

    field_encryption_key: str

    wechat_app_id: str = ""
    wechat_app_secret: str = ""
    wechat_redirect_uri: str = ""

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@example.com"

    # MiniMax 是 v1 唯一 LLM 供应商
    minimax_api_key: str = ""
    minimax_group_id: str = ""
    minimax_api_base: str = "https://api.minimax.chat/v1"

    sentry_dsn: str = ""
    posthog_api_key: str = ""
    posthog_host: str = "https://us.i.posthog.com"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
