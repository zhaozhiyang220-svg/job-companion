import pytest
from fastapi.testclient import TestClient

from src.core import config
from src.main import app


def test_dashboard_requires_password(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INTERNAL_DASHBOARD_PASSWORD", "x")
    config.get_settings.cache_clear()
    c = TestClient(app)
    r = c.get("/internal/dashboard/summary")
    assert r.status_code == 401
    config.get_settings.cache_clear()


def test_dashboard_with_password_returns(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INTERNAL_DASHBOARD_PASSWORD", "x")
    config.get_settings.cache_clear()
    c = TestClient(app)
    r = c.get("/internal/dashboard/summary", headers={"X-Internal-Password": "x"})
    assert r.status_code == 200
    assert "dau" in r.json()
    config.get_settings.cache_clear()


def test_timeseries_returns_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INTERNAL_DASHBOARD_PASSWORD", "x")
    config.get_settings.cache_clear()
    c = TestClient(app)
    r = c.get(
        "/internal/dashboard/timeseries?days=7", headers={"X-Internal-Password": "x"}
    )
    assert r.status_code == 200
    assert len(r.json()["daily"]) == 7
    config.get_settings.cache_clear()
