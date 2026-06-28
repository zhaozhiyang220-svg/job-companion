from fastapi.testclient import TestClient

from src.main import app


def test_wechat_qr_returns_url_and_state() -> None:
    client = TestClient(app)
    r = client.get("/api/v1/auth/wechat/qr")
    assert r.status_code == 200
    body = r.json()
    assert "qrconnect" in body["qr_url"]
    assert len(body["state"]) > 10


def test_wechat_callback_dev_mode_creates_user() -> None:
    # .env 的 APP_ENV=development 使 DEV- 前缀走 mock 路径
    client = TestClient(app)
    r = client.get("/api/v1/auth/wechat/callback?code=DEV-abc&state=s")
    assert r.status_code == 200
    assert r.json()["user_id"]
