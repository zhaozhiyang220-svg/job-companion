import json
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from src.services.resume_scorer import score_branch


@pytest.mark.asyncio
async def test_score_returns_int() -> None:
    with patch(
        "src.services.resume_scorer._llm.acomplete",
        AsyncMock(return_value=json.dumps({"score": 82})),
    ):
        s = await score_branch({}, {}, uuid4())
    assert s == 82
