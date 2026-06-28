import secrets

import httpx

from src.core.config import get_settings

OPEN_PLATFORM_QR_URL = "https://open.weixin.qq.com/connect/qrconnect"


def build_qr_url() -> tuple[str, str]:
    s = get_settings()
    state = secrets.token_urlsafe(16)
    qr = (
        f"{OPEN_PLATFORM_QR_URL}?appid={s.wechat_app_id}"
        f"&redirect_uri={s.wechat_redirect_uri}"
        f"&response_type=code&scope=snsapi_login&state={state}#wechat_redirect"
    )
    return qr, state


async def exchange_code_for_openid(code: str) -> str:
    s = get_settings()
    # 非生产环境提供 mock 路径（本地/CI 无法对接微信开放平台公网回调）
    if s.app_env in ("development", "test") and code.startswith("DEV-"):
        return f"openid-dev-{code[4:]}"
    url = "https://api.weixin.qq.com/sns/oauth2/access_token"
    async with httpx.AsyncClient() as client:
        r = await client.get(
            url,
            params={
                "appid": s.wechat_app_id,
                "secret": s.wechat_app_secret,
                "code": code,
                "grant_type": "authorization_code",
            },
        )
        data = r.json()
        if "openid" not in data:
            raise RuntimeError(f"wechat exchange failed: {data}")
        openid: str = data["openid"]
        return openid
