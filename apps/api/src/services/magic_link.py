import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from src.models.magic_link_token import MagicLinkToken
from src.services.email_sender import send_email

TOKEN_TTL_MINUTES = 15


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def request_link(db: Session, email: str, base_url: str) -> None:
    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash(raw_token)
    email_hash = _hash(email.lower().strip())
    expires = datetime.now(UTC) + timedelta(minutes=TOKEN_TTL_MINUTES)
    db.add(
        MagicLinkToken(token_hash=token_hash, email_lookup_hash=email_hash, expires_at=expires)
    )
    db.commit()
    link = f"{base_url}/auth/verify?token={raw_token}"
    send_email(
        to=email,
        subject="登录 Job Companion",
        html=f'<a href="{link}">点击登录（15 分钟有效）</a>',
    )


def verify_token(db: Session, raw_token: str) -> str | None:
    """成功返回 email_lookup_hash，失败返回 None。"""
    th = _hash(raw_token)
    row = db.query(MagicLinkToken).filter(MagicLinkToken.token_hash == th).first()
    if not row or row.consumed_at or row.expires_at < datetime.now(UTC):
        return None
    row.consumed_at = datetime.now(UTC)
    db.commit()
    return row.email_lookup_hash
