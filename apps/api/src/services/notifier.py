import httpx

from src.core.config import get_settings
from src.services.email_sender import send_email


async def notify_pm(message: str) -> None:
    s = get_settings()
    if s.notifier_type == "feishu" and s.feishu_webhook_url:
        async with httpx.AsyncClient() as c:
            await c.post(
                s.feishu_webhook_url,
                json={"msg_type": "text", "content": {"text": message}},
            )
    elif s.notifier_type == "telegram" and s.telegram_bot_token and s.telegram_chat_id:
        url = f"https://api.telegram.org/bot{s.telegram_bot_token}/sendMessage"
        async with httpx.AsyncClient() as c:
            await c.post(url, json={"chat_id": s.telegram_chat_id, "text": message})
    elif s.notifier_type == "email" and s.smtp_host:
        send_email(to=s.smtp_from, subject="[JC] Coach Inquiry", html=f"<pre>{message}</pre>")
    else:
        print(f"[NOTIFY-PM] {message}")
