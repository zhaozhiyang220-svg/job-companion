from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from src.main import app


def test_health_ai_returns_ok_when_llm_ok() -> None:
    with patch(
        "src.routers.health.LLMClient.acomplete", new=AsyncMock(return_value="pong")
    ):
        client = TestClient(app)
        res = client.get("/api/v1/health/ai")
        assert res.status_code == 200
        body = res.json()
        assert body["status"] == "ok"
        assert "latency_ms" in body


def test_health_ai_degraded_when_no_pong() -> None:
    with patch(
        "src.routers.health.LLMClient.acomplete", new=AsyncMock(return_value="nope")
    ):
        client = TestClient(app)
        res = client.get("/api/v1/health/ai")
        assert res.status_code == 200
        assert res.json()["status"] == "degraded"
