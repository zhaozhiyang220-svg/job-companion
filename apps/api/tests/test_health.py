from fastapi.testclient import TestClient

from src.main import app


def test_health_returns_ok() -> None:
    client = TestClient(app)
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}
