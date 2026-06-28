from datetime import UTC, datetime

from fastapi.testclient import TestClient

from src.core.db import SessionLocal
from src.core.security import issue_session_token
from src.main import app
from src.models import Application, JobPosting, User


def _setup() -> tuple[TestClient, str]:
    db = SessionLocal()
    u = User(preferences={})
    db.add(u)
    db.commit()
    db.refresh(u)
    a = Application(user_id=u.id)
    a.job_posting = JobPosting(raw_text="x")
    db.add(a)
    db.commit()
    app_id = str(a.id)
    token = issue_session_token(u.id)
    db.close()
    c = TestClient(app)
    c.cookies.set("jc_session", token)
    return c, app_id


def test_create_and_list_investment() -> None:
    c, app_id = _setup()
    body = {
        "action_type": "submitted",
        "action_at": datetime.now(UTC).isoformat(),
        "channel": "Boss直聘",
        "notes": "投了",
    }
    r = c.post(f"/api/v1/applications/{app_id}/investments", json=body)
    assert r.status_code == 201
    lst = c.get(f"/api/v1/applications/{app_id}/investments")
    assert len(lst.json()) == 1
    assert lst.json()[0]["channel"] == "Boss直聘"


def test_update_and_delete() -> None:
    c, app_id = _setup()
    r = c.post(
        f"/api/v1/applications/{app_id}/investments",
        json={"action_type": "submitted", "action_at": datetime.now(UTC).isoformat()},
    )
    iv_id = r.json()["id"]
    p = c.patch(
        f"/api/v1/applications/{app_id}/investments/{iv_id}", json={"notes": "更新"}
    )
    assert p.json()["notes"] == "更新"
    d = c.delete(f"/api/v1/applications/{app_id}/investments/{iv_id}")
    assert d.status_code == 204
