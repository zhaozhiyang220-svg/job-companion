import json
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from src.core.db import SessionLocal
from src.core.security import issue_session_token
from src.main import app
from src.models import AbilityCard, MasterResume, User


def _setup() -> tuple[TestClient, str]:
    db = SessionLocal()
    u = User(preferences={})
    db.add(u)
    db.commit()
    db.refresh(u)
    r = MasterResume(user_id=u.id)
    db.add(r)
    db.flush()
    a = AbilityCard(master_resume_id=r.id, skill_name="Python", level=3)
    db.add(a)
    db.commit()
    aid = str(a.id)
    c = TestClient(app)
    c.cookies.set("jc_session", issue_session_token(u.id))
    db.close()
    return c, aid


def test_diagnose_marks_weak() -> None:
    c, aid = _setup()
    fake = {
        "overall_score": 65,
        "weak_cards": [{"type": "ability", "id": aid, "reasons": ["evidence missing"]}],
    }
    with patch(
        "src.services.quality_diagnoser._llm.acomplete",
        AsyncMock(return_value=json.dumps(fake)),
    ):
        r = c.post("/api/v1/master-resume/diagnose")
    assert r.status_code == 200
    assert r.json()["overall_score"] == 65
