from unittest.mock import AsyncMock, patch

import pytest

from src.core import config
from src.services.notifier import notify_pm


@pytest.mark.asyncio
async def test_print_mode_no_http(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("NOTIFIER_TYPE", "print")
    config.get_settings.cache_clear()
    await notify_pm("hello PM")
    out = capsys.readouterr().out
    assert "hello PM" in out


@pytest.mark.asyncio
async def test_feishu_mode_posts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOTIFIER_TYPE", "feishu")
    monkeypatch.setenv("FEISHU_WEBHOOK_URL", "https://test.feishu/x")
    config.get_settings.cache_clear()
    with patch("httpx.AsyncClient.post", AsyncMock()) as mp:
        await notify_pm("ping")
        mp.assert_awaited_once()
    config.get_settings.cache_clear()
