import json
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from src.services.patch_generator import generate_patch


@pytest.mark.asyncio
async def test_generate_patch() -> None:
    fake = {
        "patch": [{"type": "emphasize", "card_id": "a1", "intensity": "high"}],
        "reasoning": [{"op_index": 0, "reason": "JD 强调此能力"}],
    }
    with patch(
        "src.services.patch_generator._llm.acomplete",
        AsyncMock(return_value=json.dumps(fake)),
    ):
        out = await generate_patch(
            {"ability_cards": [{"id": "a1", "skill_name": "增长"}]},
            {"company_name": "字节", "requirements": {"hard": ["增长"]}},
            "zh",
            uuid4(),
        )
    assert out["patch"][0]["intensity"] == "high"  # type: ignore[index]
    assert "JD 强调" in out["reasoning"][0]["reason"]  # type: ignore[index]


@pytest.mark.asyncio
async def test_generate_patch_invalid_raises() -> None:
    with (
        patch(
            "src.services.patch_generator._llm.acomplete",
            AsyncMock(return_value=json.dumps({"foo": "bar"})),
        ),
        pytest.raises(ValueError),
    ):
        await generate_patch({}, {}, "zh", uuid4())
