from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class WeeklyOut(BaseModel):
    id: UUID
    week_of: date
    stats: dict[str, object]
    ai_observation_text: str
    suggested_actions: list[dict[str, object]]
    generated_at: datetime


class WeeklyHistoryItem(BaseModel):
    week_of: date
    stats: dict[str, object]
