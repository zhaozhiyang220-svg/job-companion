import json
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from src.services.weekly_observer import generate_observation


@pytest.mark.asyncio
async def test_observation() -> None:
    fake = {
        "text": "本周 75% 在增长方向",
        "suggested_actions": [{"label": "补强数据卡", "url": None}],
    }
    with patch(
        "src.services.weekly_observer._llm.acomplete",
        AsyncMock(return_value=json.dumps(fake)),
    ):
        out = await generate_observation({"new_applications": 4}, [{"company": "字节"}], uuid4())
    assert "增长" in out["text"]
