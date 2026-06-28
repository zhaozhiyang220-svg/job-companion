from unittest.mock import AsyncMock, patch

import pytest

from src.ai.llm_client import LLMClient


@pytest.mark.asyncio
async def test_acomplete_returns_text() -> None:
    message = type("M", (), {"content": "ok"})()
    choice = type("C", (), {"message": message})()
    fake_response = type("R", (), {"choices": [choice]})()

    with patch(
        "src.ai.llm_client.acompletion", new=AsyncMock(return_value=fake_response)
    ) as mocked:
        client = LLMClient()
        out = await client.acomplete(
            model="minimax/abab6.5s-chat",
            system="you are helpful",
            messages=[{"role": "user", "content": "hi"}],
        )
        assert out == "ok"
        mocked.assert_awaited_once()


@pytest.mark.asyncio
async def test_acomplete_falls_back_to_second_model() -> None:
    message = type("M", (), {"content": "fallback-ok"})()
    choice = type("C", (), {"message": message})()
    fake_response = type("R", (), {"choices": [choice]})()

    async def flaky(model: str, **_: object) -> object:
        if model == "minimax/MiniMax-M1":
            raise RuntimeError("rate limited")
        return fake_response

    with patch("src.ai.llm_client.acompletion", new=AsyncMock(side_effect=flaky)):
        out = await LLMClient().acomplete(
            model="auto-m1",
            system="s",
            messages=[{"role": "user", "content": "hi"}],
        )
        assert out == "fallback-ok"
