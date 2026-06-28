from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from src.core.db import SessionLocal
from src.core.security import issue_session_token
from src.main import app
from src.models import User


def _login() -> TestClient:
    db = SessionLocal()
    u = User(preferences={})
    db.add(u)
    db.commit()
    db.refresh(u)
    token = issue_session_token(u.id)
    db.close()
    c = TestClient(app)
    c.cookies.set("jc_session", token)
    return c


def test_get_weekly_returns() -> None:
    c = _login()
    with patch(
        "src.services.weekly_digester.generate_observation",
        AsyncMock(return_value={"text": "ok", "suggested_actions": []}),
    ):
        r = c.get("/api/v1/weekly")
    assert r.status_code == 200
    assert r.json()["ai_observation_text"] == "ok"
    assert "stats" in r.json()


def test_refresh_and_history() -> None:
    c = _login()
    with patch(
        "src.services.weekly_digester.generate_observation",
        AsyncMock(return_value={"text": "refreshed", "suggested_actions": []}),
    ):
        rr = c.post("/api/v1/weekly/refresh")
    assert rr.status_code == 200
    assert rr.json()["ai_observation_text"] == "refreshed"

    h = c.get("/api/v1/weekly/history?weeks=4")
    assert h.status_code == 200
    assert len(h.json()) == 1
