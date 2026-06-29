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


@pytest.mark.asyncio
async def test_logging_failure_does_not_break_call() -> None:
    # 落库失败（如表缺失/连接断）时，AI 主流程仍应正常返回，而非 500。
    message = type("M", (), {"content": "ok"})()
    choice = type("C", (), {"message": message})()
    fake_response = type("R", (), {"choices": [choice]})()
    broken_session = MagicMock()
    broken_session.commit.side_effect = RuntimeError("relation does not exist")
    with (
        patch("src.ai.llm_client.acompletion", AsyncMock(return_value=fake_response)),
        patch("src.ai.llm_client.SessionLocal", return_value=broken_session),
    ):
        out = await LLMClient().acomplete(
            "deepseek/deepseek-chat",
            "sys",
            [{"role": "user", "content": "hi"}],
            scene="test_resilient",
        )
    assert out == "ok"
