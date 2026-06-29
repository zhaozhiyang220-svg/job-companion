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

    # 对外可访问的 Web 地址（magic-link 邮件里的链接 base）。
    # 本机默认 localhost；生产设成 http://<公网IP> 或正式域名。
    public_web_url: str = "http://localhost:3000"

    wechat_app_id: str = ""
    wechat_app_secret: str = ""
    wechat_redirect_uri: str = ""

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@example.com"

    # v1 实际跑 DeepSeek（LiteLLM 原生支持，读 DEEPSEEK_API_KEY）
    deepseek_api_key: str = ""

    # MiniMax 为最初设计的供应商，暂保留为 legacy（未启用）
    minimax_api_key: str = ""
    minimax_group_id: str = ""
    minimax_api_base: str = "https://api.minimax.chat/v1"

    sentry_dsn: str = ""
    posthog_api_key: str = ""
    posthog_host: str = "https://us.i.posthog.com"

    s3_bucket: str = ""
    s3_region: str = "us-east-1"
    s3_endpoint_url: str | None = None
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""

    notifier_type: str = "print"  # print | feishu | telegram | email
    feishu_webhook_url: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    internal_dashboard_password: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
