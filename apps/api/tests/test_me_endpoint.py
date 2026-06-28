from fastapi.testclient import TestClient

from src.core.db import SessionLocal
from src.core.security import issue_session_token
from src.main import app
from src.models import User


def _login_as_new_user() -> tuple[TestClient, str]:
    db = SessionLocal()
    u = User(preferences={})
    db.add(u)
    db.commit()
    db.refresh(u)
    uid = str(u.id)
    db.close()
    client = TestClient(app)
    client.cookies.set("jc_session", issue_session_token(u.id))
    return client, uid


def test_me_returns_user() -> None:
    client, uid = _login_as_new_user()
    r = client.get("/api/v1/me")
    assert r.status_code == 200
    assert r.json()["id"] == uid


def test_me_patch_persona() -> None:
    client, _ = _login_as_new_user()
    r = client.patch(
        "/api/v1/me", json={"persona_type": "job_hopper", "nickname": "张三"}
    )
    assert r.status_code == 200
    assert r.json()["persona_type"] == "job_hopper"
    assert r.json()["nickname"] == "张三"


def test_me_without_cookie_401() -> None:
    client = TestClient(app)
    r = client.get("/api/v1/me")
    assert r.status_code == 401
