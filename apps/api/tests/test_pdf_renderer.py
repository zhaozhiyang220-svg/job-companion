from unittest.mock import MagicMock, patch

import pytest

try:
    import weasyprint  # noqa: F401

    _HAS_WEASYPRINT = True
except Exception:  # noqa: BLE001  原生库缺失（Windows）时 import 抛 OSError
    _HAS_WEASYPRINT = False


@pytest.mark.skipif(not _HAS_WEASYPRINT, reason="weasyprint native libs unavailable")
def test_render_pdf_returns_bytes() -> None:
    from src.services.pdf_renderer import render_pdf

    with patch("weasyprint.HTML") as mock_html:
        mock_html.return_value.write_pdf.return_value = b"%PDF-fake"
        out = render_pdf("<html></html>")
    assert out.startswith(b"%PDF")


def test_export_endpoint_uploads_and_returns_url() -> None:
    from fastapi.testclient import TestClient

    from src.core.db import SessionLocal
    from src.core.security import issue_session_token
    from src.main import app
    from src.models import AbilityCard, Application, JobPosting, MasterResume, ResumeBranch, User

    db = SessionLocal()
    u = User(preferences={})
    db.add(u)
    db.commit()
    db.refresh(u)
    r = MasterResume(user_id=u.id, basic_info={"name": "张三"})
    db.add(r)
    db.flush()
    db.add(AbilityCard(master_resume_id=r.id, skill_name="增长"))
    appl = Application(user_id=u.id)
    appl.job_posting = JobPosting(raw_text="x", language="zh")
    db.add(appl)
    db.flush()
    branch = ResumeBranch(application_id=appl.id, version_label="v1", patch=[], language="zh")
    db.add(branch)
    db.commit()
    app_id, branch_id = str(appl.id), str(branch.id)
    token = issue_session_token(u.id)
    db.close()

    client = TestClient(app)
    client.cookies.set("jc_session", token)

    mock_cli = MagicMock()
    with (
        patch("src.routers.resume_branch.render_pdf", return_value=b"%PDF-fake"),
        patch("src.routers.resume_branch._client", return_value=mock_cli),
        patch("src.routers.resume_branch.presign_get", return_value="https://s3/exported.pdf"),
    ):
        res = client.post(
            f"/api/v1/applications/{app_id}/branches/{branch_id}/export",
            json={"language": "zh", "mask_current_company": True},
        )
    assert res.status_code == 200
    assert res.json()["pdf_url"] == "https://s3/exported.pdf"
    mock_cli.put_object.assert_called_once()
