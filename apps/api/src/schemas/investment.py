from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.models.investment import InvestmentActionType


class CreateInvestmentIn(BaseModel):
    action_type: InvestmentActionType
    action_at: datetime
    channel: str = ""
    notes: str = ""
    used_resume_branch_id: UUID | None = None


class UpdateInvestmentIn(BaseModel):
    action_type: InvestmentActionType | None = None
    action_at: datetime | None = None
    channel: str | None = None
    notes: str | None = None
    used_resume_branch_id: UUID | None = None


class InvestmentOut(BaseModel):
    id: UUID
    action_type: InvestmentActionType
    action_at: datetime
    channel: str
    notes: str
    used_resume_branch_id: UUID | None
    used_branch_label: str | None  # 渲染时拼出 "v2 · 82"
