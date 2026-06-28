from datetime import date

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    dau: int
    mau: int
    total_users: int
    ai_calls_today: int
    ai_cost_today_usd: float
    ai_calls_30d: int
    ai_cost_30d_usd: float
    coach_inquiries_week: int


class DailyRow(BaseModel):
    date: date
    dau: int
    ai_calls: int
    ai_cost: float


class TimeSeries(BaseModel):
    daily: list[DailyRow]
