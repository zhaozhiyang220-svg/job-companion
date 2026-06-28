from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from src.core.db import SessionLocal
from src.core.security import issue_session_token
from src.main import app
from src.models import CoachInquiry, User


def _login() -> TestClient:
    db = SessionLocal()
    db.query(CoachInquiry).delete()
    u = User(preferences={})
    db.add(u)
    db.commit()
    db.refresh(u)
    token = issue_session_token(u.id)
    db.close()
    c = TestClient(app)
    c.cookies.set("jc_session", token)
    return c


def test_availability_starts_open() -> None:
    c = _login()
    r = c.get("/api/v1/coach/availability")
    assert r.status_code == 200
    assert r.json()["available"] is True


def test_create_inquiry_notifies() -> None:
    c = _login()
    with patch("src.routers.coach.notify_pm", AsyncMock()) as mp:
        r = c.post(
            "/api/v1/coach/inquiries",
            json={"source_screen": "resume_workspace", "contact_method": "wx:test"},
        )
    assert r.status_code == 201
    mp.assert_awaited_once()


def test_capacity_full() -> None:
    c = _login()
    with patch("src.routers.coach.notify_pm", AsyncMock()):
        for _ in range(5):
            c.post(
                "/api/v1/coach/inquiries",
                json={"source_screen": "x", "contact_method": "y"},
            )
        r = c.post(
            "/api/v1/coach/inquiries", json={"source_screen": "x", "contact_method": "y"}
        )
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "coach_full"
