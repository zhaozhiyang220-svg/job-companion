import json
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from src.models import PersonaType
from src.services.resume_parser import parse_resume_text

FAKE = {
    "basic_info": {"name": "张三", "phone": None, "email": None, "location": "北京"},
    "ability_cards": [
        {
            "skill_name": "增长",
            "evidence_text": "",
            "level": 4,
            "last_used_year": 2024,
            "tags": [],
        }
    ],
    "project_cards": [],
    "experience_cards": [
        {
            "company": "字节",
            "period": "2020-至今",
            "title": "PM",
            "scope": "",
            "achievements": [],
            "industry": "互联网",
            "is_current": True,
        }
    ],
}


@pytest.mark.asyncio
async def test_parse_returns_pydantic() -> None:
    with patch(
        "src.services.resume_parser._llm.acomplete",
        AsyncMock(return_value=json.dumps(FAKE)),
    ):
        out = await parse_resume_text("any text", PersonaType.JOB_HOPPER, uuid4())
    assert out.basic_info["name"] == "张三"
    assert out.experience_cards[0].is_current is True
    assert out.ability_cards[0].skill_name == "增长"
