from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class InvestmentActionType(StrEnum):
    SUBMITTED = "submitted"
    VIEWED = "viewed"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    OFFER_RECEIVED = "offer_received"
    REJECTED = "rejected"


class Investment(Base):
    __tablename__ = "investments"

    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid4)
    application_id: Mapped[UUID] = mapped_column(
        sa.Uuid, ForeignKey("applications.id"), index=True
    )
    used_resume_branch_id: Mapped[UUID | None] = mapped_column(
        sa.Uuid, ForeignKey("resume_branches.id"), nullable=True
    )
    action_type: Mapped[InvestmentActionType] = mapped_column(
        sa.Enum(InvestmentActionType, name="investment_action_enum"), index=True
    )
    action_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    channel: Mapped[str] = mapped_column(String(64), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa.func.now()
    )
