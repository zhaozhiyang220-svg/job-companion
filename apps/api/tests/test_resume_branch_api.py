from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from src.core.db import SessionLocal
from src.core.security import issue_session_token
from src.main import app
from src.models import AbilityCard, Application, JobPosting, MasterResume, User


def _setup() -> tuple[TestClient, str, str]:
    db = SessionLocal()
    u = User(preferences={})
    db.add(u)
    db.commit()
    db.refresh(u)
    r = MasterResume(user_id=u.id)
    db.add(r)
    db.flush()
    a_card = AbilityCard(master_resume_id=r.id, skill_name="增长")
    db.add(a_card)
    db.flush()
    appl = Application(user_id=u.id)
    appl.job_posting = JobPosting(raw_text="...", company_name="字节", language="zh")
    db.add(appl)
    db.commit()
    app_id = str(appl.id)
    a_id = str(a_card.id)
    c = TestClient(app)
    c.cookies.set("jc_session", issue_session_token(u.id))
    db.close()
    return c, app_id, a_id


def test_create_branch_generates_patch_and_score() -> None:
    c, app_id, a_id = _setup()
    fake_patch = {
        "patch": [{"type": "emphasize", "card_id": a_id, "intensity": "high"}],
        "reasoning": [{"op_index": 0, "reason": "JD 强调增长"}],
    }
    with (
        patch("src.routers.resume_branch.generate_patch", AsyncMock(return_value=fake_patch)),
        patch("src.routers.resume_branch.score_branch", AsyncMock(return_value=82)),
    ):
        r = c.post(f"/api/v1/applications/{app_id}/branches", json={})
    assert r.status_code == 201
    b = r.json()
    assert b["match_score"] == 82
    assert b["version_label"] == "v1"
    assert b["rendered_resume"]["ability_cards"][0]["_emphasized"] == "high"


def test_list_and_rollback() -> None:
    c, app_id, a_id = _setup()
    fake_patch = {
        "patch": [{"type": "emphasize", "card_id": a_id, "intensity": "high"}],
        "reasoning": [{"op_index": 0, "reason": "x"}],
    }
    with (
        patch("src.routers.resume_branch.generate_patch", AsyncMock(return_value=fake_patch)),
        patch("src.routers.resume_branch.score_branch", AsyncMock(return_value=70)),
    ):
        v1 = c.post(f"/api/v1/applications/{app_id}/branches", json={}).json()
        c.post(f"/api/v1/applications/{app_id}/branches", json={})

    lst = c.get(f"/api/v1/applications/{app_id}/branches").json()
    assert len(lst) == 2

    rb = c.post(f"/api/v1/applications/{app_id}/branches/{v1['id']}/rollback-to/{v1['id']}")
    assert rb.status_code == 200
    assert rb.json()["version_label"] == "v3"
    assert rb.json()["is_active"] is True
