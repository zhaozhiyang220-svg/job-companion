import json
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from src.core.db import SessionLocal
from src.core.security import issue_session_token
from src.main import app
from src.models import PersonaType, User


def _login_fresh_grad() -> TestClient:
    db = SessionLocal()
    u = User(preferences={}, persona_type=PersonaType.FRESH_GRAD)
    db.add(u)
    db.commit()
    db.refresh(u)
    c = TestClient(app)
    c.cookies.set("jc_session", issue_session_token(u.id))
    db.close()
    return c


def test_intake_flow() -> None:
    c = _login_fresh_grad()
    r = c.post("/api/v1/master-resume/intake/start")
    assert r.status_code == 200
    sid = r.json()["session_id"]
    assert r.json()["first_question"]

    with patch(
        "src.services.intake._llm.acomplete",
        AsyncMock(return_value=json.dumps({"done": False, "next_question": "再说一个"})),
    ):
        r = c.post(
            "/api/v1/master-resume/intake/answer",
            json={"session_id": sid, "answer": "我做了 X"},
        )
        assert r.json()["done"] is False
        assert r.json()["next_question"] == "再说一个"

    with patch(
        "src.services.intake._llm.acomplete",
        AsyncMock(return_value=json.dumps({"done": True, "summary": "ok"})),
    ):
        r = c.post(
            "/api/v1/master-resume/intake/answer",
            json={"session_id": sid, "answer": "再补充"},
        )
        assert r.json()["done"] is True
