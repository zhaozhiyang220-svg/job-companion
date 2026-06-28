from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from src.core.db import SessionLocal
from src.core.security import issue_session_token
from src.main import app
from src.models import User
from src.schemas.resume import ExperienceIn, ParsedResume


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


def test_upload_init_returns_url() -> None:
    with patch(
        "src.routers.master_resume.presign_put", return_value="https://up.example.com"
    ):
        c = _login()
        r = c.post(
            "/api/v1/master-resume/upload-init",
            json={"filename": "r.pdf", "content_type": "application/pdf"},
        )
    assert r.status_code == 200
    assert r.json()["upload_url"].startswith("https://")


def test_parse_creates_resume() -> None:
    fake_parsed = ParsedResume(
        basic_info={"name": "张三"},
        ability_cards=[],
        project_cards=[],
        experience_cards=[ExperienceIn(company="字节", title="PM", is_current=True)],
    )
    with (
        patch("src.routers.master_resume.download_bytes", return_value=b"x"),
        patch("src.routers.master_resume.extract_text", return_value="some text"),
        patch(
            "src.routers.master_resume.parse_resume_text",
            AsyncMock(return_value=fake_parsed),
        ),
    ):
        c = _login()
        r = c.post(
            "/api/v1/master-resume/parse", json={"s3_key": "users/x/resumes/y.pdf"}
        )
    assert r.status_code == 200
    body = r.json()
    assert body["basic_info"]["name"] == "张三"
    assert body["experience_cards"][0]["company"] == "字节"
    assert body["experience_cards"][0]["is_current"] is True
