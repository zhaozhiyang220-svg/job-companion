import json
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from src.services.jd_parser import parse_jd


@pytest.mark.asyncio
async def test_parse_jd() -> None:
    fake = {
        "company_name": "字节",
        "job_title": "PM",
        "department": "豆包",
        "salary_range": "24-40k",
        "location": "北京",
        "language": "zh",
        "requirements": {"hard": ["PM 经验"], "soft": ["主动"], "years": "3-5"},
        "hidden_preferences": ["抗压"],
        "red_flags": [],
    }
    with patch(
        "src.services.jd_parser._llm.acomplete", AsyncMock(return_value=json.dumps(fake))
    ):
        out = await parse_jd("...", uuid4())
    assert out.company_name == "字节"
    assert out.requirements.hard == ["PM 经验"]
    assert out.hidden_preferences == ["抗压"]
