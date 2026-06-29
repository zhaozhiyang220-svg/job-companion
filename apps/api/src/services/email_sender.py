import smtplib
from email.message import EmailMessage

from src.core.config import get_settings


def send_email(to: str, subject: str, html: str) -> None:
    s = get_settings()
    if s.app_env == "development" or not s.smtp_host:
        # dev 模式不真发邮件，打印到日志（隐私：仅本地）
        print(f"[DEV EMAIL] to={to} subject={subject}\n{html}")
        return
    msg = EmailMessage()
    msg["From"] = s.smtp_from
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(html, subtype="html")
    # 465 为隐式 SSL（QQ/腾讯企业邮推荐），其余端口（如 587）走 STARTTLS。
    if s.smtp_port == 465:
        with smtplib.SMTP_SSL(s.smtp_host, s.smtp_port) as srv:
            srv.login(s.smtp_user, s.smtp_password)
            srv.send_message(msg)
    else:
        with smtplib.SMTP(s.smtp_host, s.smtp_port) as srv:
            srv.starttls()
            srv.login(s.smtp_user, s.smtp_password)
            srv.send_message(msg)
