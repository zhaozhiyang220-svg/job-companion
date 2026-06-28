import secrets
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from src.core.db import SessionLocal
from src.main import app
from src.models import User
from src.models.magic_link_token import MagicLinkToken
from src.services.magic_link import _hash, verify_token


def _insert_token(raw: str, email: str, *, minutes: int = 15) -> None:
    db = SessionLocal()
    db.add(
        MagicLinkToken(
            token_hash=_hash(raw),
            email_lookup_hash=_hash(email),
            expires_at=datetime.now(UTC) + timedelta(minutes=minutes),
        )
    )
    db.commit()
    db.close()


def test_request_creates_token() -> None:
    client = TestClient(app)
    r = client.post("/api/v1/auth/magic-link/request", json={"email": "req@test.com"})
    assert r.status_code == 200
    assert r.json() == {"sent": True}

    db = SessionLocal()
    row = (
        db.query(MagicLinkToken)
        .filter(MagicLinkToken.email_lookup_hash == _hash("req@test.com"))
        .first()
    )
    assert row is not None
    db.close()


def test_invalid_token_rejected() -> None:
    client = TestClient(app)
    r = client.post("/api/v1/auth/magic-link/verify", json={"token": "bogus-token"})
    assert r.status_code == 400


def test_verify_endpoint_creates_user() -> None:
    raw = secrets.token_urlsafe(32)
    _insert_token(raw, "newuser@test.com")
    client = TestClient(app)
    r = client.post("/api/v1/auth/magic-link/verify", json={"token": raw})
    assert r.status_code == 200
    assert r.json()["user_id"]

    db = SessionLocal()
    user = db.query(User).filter(User.email_lookup_hash == _hash("newuser@test.com")).first()
    assert user is not None
    db.close()


def test_verify_token_single_use() -> None:
    raw = secrets.token_urlsafe(32)
    _insert_token(raw, "single@test.com")
    db = SessionLocal()
    assert verify_token(db, raw) == _hash("single@test.com")
    assert verify_token(db, raw) is None  # 二次消费失败
    db.close()
