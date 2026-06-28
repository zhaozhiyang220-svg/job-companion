import json
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from src.models.resource_item import ResourceType
from src.services.resource_processor import summarize


@pytest.mark.asyncio
async def test_summarize() -> None:
    fake = {
        "summary": "豆包二面偏业务",
        "signals": [{"type": "question_pattern", "content": "必问北极星指标"}],
        "companies": ["字节"],
    }
    with patch(
        "src.services.resource_processor._llm.acomplete",
        AsyncMock(return_value=json.dumps(fake)),
    ):
        out = await summarize("面经原文...", ResourceType.INTERVIEW_RECALL, uuid4())
    assert "北极星" in out["signals"][0]["content"]
    assert out["companies"] == ["字节"]
