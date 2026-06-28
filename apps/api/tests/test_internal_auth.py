import pytest
from fastapi import HTTPException

from src.core import config
from src.core.internal_auth import require_internal_password


def test_rejects_wrong_password(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INTERNAL_DASHBOARD_PASSWORD", "s3cret")
    config.get_settings.cache_clear()
    with pytest.raises(HTTPException) as ei:
        require_internal_password(x_internal_password="wrong")
    assert ei.value.status_code == 401
    config.get_settings.cache_clear()


def test_accepts_correct_password(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INTERNAL_DASHBOARD_PASSWORD", "s3cret")
    config.get_settings.cache_clear()
    require_internal_password(x_internal_password="s3cret")  # 不抛异常
    config.get_settings.cache_clear()
