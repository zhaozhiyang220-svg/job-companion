from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from src.core.db import SessionLocal
from src.core.security import issue_session_token
from src.main import app
from src.models import User
from src.schemas.jd import JDRequirements, ParsedJD


def _login() -> TestClient:
    db = SessionLocal()
    u = User(preferences={})
    db.add(u)
    db.commit()
    db.refresh(u)
    c = TestClient(app)
    c.cookies.set("jc_session", issue_session_token(u.id))
    db.close()
    return c


def test_create_and_list_application() -> None:
    fake = ParsedJD(company_name="字节", job_title="PM", requirements=JDRequirements(hard=["PM"]))
    with patch("src.routers.application.parse_jd", AsyncMock(return_value=fake)):
        c = _login()
        r1 = c.post("/api/v1/applications", json={"raw_text": "...PM..."})
        assert r1.status_code == 201
        assert r1.json()["job_posting"]["company_name"] == "字节"

        r2 = c.get("/api/v1/applications")
        assert r2.json()["total"] == 1


def test_capacity_limit_triggers() -> None:
    # 月新建上限 15 < 进行中上限 20，所以全新创建场景下 capacity_monthly 先触发。
    fake = ParsedJD()
    with patch("src.routers.application.parse_jd", AsyncMock(return_value=fake)):
        c = _login()
        for _ in range(15):
            assert c.post("/api/v1/applications", json={"raw_text": "x"}).status_code == 201
        r = c.post("/api/v1/applications", json={"raw_text": "x"})
        assert r.status_code == 409
        assert r.json()["detail"]["code"] == "capacity_monthly"


def test_archive_then_get() -> None:
    fake = ParsedJD(company_name="腾讯", job_title="后端")
    with patch("src.routers.application.parse_jd", AsyncMock(return_value=fake)):
        c = _login()
        created = c.post("/api/v1/applications", json={"raw_text": "x"}).json()
        aid = created["id"]
        r = c.patch(f"/api/v1/applications/{aid}", json={"status": "archived"})
        assert r.status_code == 200
        assert r.json()["status"] == "archived"
        got = c.get(f"/api/v1/applications/{aid}")
        assert got.json()["job_posting"]["company_name"] == "腾讯"
