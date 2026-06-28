from fastapi.testclient import TestClient

from src.core.db import SessionLocal
from src.core.security import issue_session_token
from src.main import app
from src.models import MasterResume, User


def _login_with_resume() -> TestClient:
    db = SessionLocal()
    u = User(preferences={})
    db.add(u)
    db.commit()
    db.refresh(u)
    r = MasterResume(user_id=u.id)
    db.add(r)
    db.commit()
    c = TestClient(app)
    c.cookies.set("jc_session", issue_session_token(u.id))
    db.close()
    return c


def test_create_update_delete_ability_card() -> None:
    c = _login_with_resume()
    r = c.post(
        "/api/v1/master-resume/cards/ability", json={"skill_name": "增长", "level": 4}
    )
    assert r.status_code == 201
    cid = r.json()["id"]
    r2 = c.patch(f"/api/v1/master-resume/cards/ability/{cid}", json={"level": 5})
    assert r2.status_code == 200
    r3 = c.delete(f"/api/v1/master-resume/cards/ability/{cid}")
    assert r3.status_code == 204


def test_create_experience_encrypts_company() -> None:
    c = _login_with_resume()
    r = c.post(
        "/api/v1/master-resume/cards/experience",
        json={"company": "字节跳动", "title": "PM", "is_current": True},
    )
    assert r.status_code == 201


def test_invalid_card_type_400() -> None:
    c = _login_with_resume()
    r = c.post("/api/v1/master-resume/cards/bogus", json={"x": 1})
    assert r.status_code == 400
