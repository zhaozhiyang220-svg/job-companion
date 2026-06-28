from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from src.core.db import SessionLocal
from src.core.security import issue_session_token
from src.main import app
from src.models import User

_NO_AI = {"summary": "", "signals": [], "companies": []}


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


def test_create_resource_with_ai_summary() -> None:
    fake = {"summary": "摘要", "signals": [], "companies": ["字节"]}
    with patch("src.routers.resource.summarize", AsyncMock(return_value=fake)):
        c = _login()
        r = c.post(
            "/api/v1/resources",
            json={"type": "interview_recall", "title": "豆包二面", "content_text": "问了北极星"},
        )
    assert r.status_code == 201
    assert r.json()["ai_summary"] == "摘要"
    assert r.json()["linked_company_names"] == ["字节"]


def test_create_collection_and_link() -> None:
    c = _login()
    cr = c.post("/api/v1/resource-collections", json={"name": "字节面试"})
    cid = cr.json()["id"]
    with patch("src.routers.resource.summarize", AsyncMock(return_value=_NO_AI)):
        rr = c.post(
            "/api/v1/resources", json={"type": "other", "title": "t", "content_text": "x"}
        )
    rid = rr.json()["id"]
    lk = c.post(f"/api/v1/resource-collections/{cid}/items/{rid}")
    assert lk.status_code == 201
    lst = c.get(f"/api/v1/resources?collection_id={cid}")
    assert lst.json()["total"] == 1

    cols = c.get("/api/v1/resource-collections").json()
    assert cols[0]["item_count"] == 1


def test_link_resource_to_application() -> None:
    from uuid import UUID

    from src.models import Application, JobPosting, ResourceItem

    c = _login()
    with patch("src.routers.resource.summarize", AsyncMock(return_value=_NO_AI)):
        rr = c.post(
            "/api/v1/resources", json={"type": "other", "title": "面经", "content_text": "x"}
        )
    rid = rr.json()["id"]

    db = SessionLocal()
    res = db.get(ResourceItem, UUID(rid))
    assert res is not None
    appl = Application(user_id=res.user_id)
    appl.job_posting = JobPosting(raw_text="x")
    db.add(appl)
    db.commit()
    app_id = str(appl.id)
    db.close()

    lk = c.post(f"/api/v1/applications/{app_id}/resources/{rid}")
    assert lk.status_code == 201
    got = c.get(f"/api/v1/applications/{app_id}/resources").json()
    assert len(got) == 1
    assert got[0]["title"] == "面经"
