import os

from posthog import Posthog

# 直接读 env（不经 Settings），避免与 config 模块产生导入期耦合。
_api_key = os.getenv("POSTHOG_API_KEY", "")
_host = os.getenv("POSTHOG_HOST", "https://us.i.posthog.com")
_client: Posthog | None = Posthog(_api_key, host=_host) if _api_key else None


def capture(user_id: str | None, event: str, props: dict[str, str] | None = None) -> None:
    """埋点；未配置 PostHog key 时静默跳过。"""
    if _client is None:
        return
    _client.capture(distinct_id=user_id or "anonymous", event=event, properties=props or {})
