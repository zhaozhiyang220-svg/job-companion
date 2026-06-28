from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.orm import Session

from src.models import User
from src.services.weekly_digester import get_or_create


@pytest.mark.asyncio
async def test_creates_when_missing(db: Session) -> None:
    u = User(preferences={})
    db.add(u)
    db.commit()
    db.refresh(u)
    with patch(
        "src.services.weekly_digester.generate_observation",
        AsyncMock(return_value={"text": "x", "suggested_actions": []}),
    ):
        d = await get_or_create(db, u.id)
    assert d.ai_observation_text == "x"


@pytest.mark.asyncio
async def test_cached_on_second_call(db: Session) -> None:
    u = User(preferences={})
    db.add(u)
    db.commit()
    db.refresh(u)
    with patch(
        "src.services.weekly_digester.generate_observation",
        AsyncMock(return_value={"text": "first", "suggested_actions": []}),
    ) as mock_ai:
        d1 = await get_or_create(db, u.id)
        d2 = await get_or_create(db, u.id)  # 命中缓存，不再调 AI
    assert d1.id == d2.id
    assert mock_ai.await_count == 1
