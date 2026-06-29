from fastapi.testclient import TestClient

from src.core.db import SessionLocal
from src.main import app
from src.models import User


def test_guest_creates_anonymous_user_and_session() -> None:
    client = TestClient(app)
    r = client.post("/api/v1/auth/guest")
    assert r.status_code == 200
    uid = r.json()["user_id"]
    assert uid
    assert "jc_session" in r.cookies

    db = SessionLocal()
    user = db.get(User, uid)
    assert user is not None
    assert user.email_lookup_hash is None  # 真匿名
    db.close()


def test_guest_is_idempotent_with_existing_session() -> None:
    client = TestClient(app)
    first = client.post("/api/v1/auth/guest")
    uid = first.json()["user_id"]
    # 已有会话 cookie，再次调用应复用同一用户而非新建
    again = client.post("/api/v1/auth/guest")
    assert again.json()["user_id"] == uid


def test_guest_session_authorizes_me() -> None:
    client = TestClient(app)
    client.post("/api/v1/auth/guest")
    me = client.get("/api/v1/me")
    assert me.status_code == 200
    assert me.json()["persona_type"] is None
