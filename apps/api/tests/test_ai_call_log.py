from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.ai.llm_client import LLMClient
from src.core.db import SessionLocal
from src.models.ai_call_log import AICallLog


@pytest.mark.asyncio
async def test_log_written_on_success() -> None:
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock(message=MagicMock(content="ok"))]
    mock_resp.usage = MagicMock(prompt_tokens=10, completion_tokens=2)
    with (
        patch("src.ai.llm_client.acompletion", AsyncMock(return_value=mock_resp)),
        patch("src.ai.llm_client.completion_cost", return_value=0.001),
    ):
        out = await LLMClient().acomplete(
            "minimax/abab6.5s-chat",
            "sys",
            [{"role": "user", "content": "hi"}],
            scene="test_log",
        )
    assert out == "ok"

    db = SessionLocal()
    row = (
        db.query(AICallLog)
        .filter(AICallLog.scene == "test_log")
        .order_by(AICallLog.created_at.desc())
        .first()
    )
    db.close()
    assert row is not None
    assert row.input_tokens == 10
    assert row.output_tokens == 2
    assert row.status == "ok"


@pytest.mark.asyncio
async def test_log_written_on_error() -> None:
    with (
        patch("src.ai.llm_client.acompletion", AsyncMock(side_effect=RuntimeError("boom"))),
        pytest.raises(RuntimeError),
    ):
        await LLMClient().acomplete(
            "minimax/abab6.5s-chat",
            "sys",
            [{"role": "user", "content": "hi"}],
            scene="test_err",
        )
    db = SessionLocal()
    row = db.query(AICallLog).filter(AICallLog.scene == "test_err").first()
    db.close()
    assert row is not None
    assert row.status == "error"
