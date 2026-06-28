from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class CoachInquiryStatus(StrEnum):
    NEW = "new"
    CONTACTED = "contacted"
    SCHEDULED = "scheduled"
    CONVERTED = "converted"
    DROPPED = "dropped"


class CoachInquiry(Base):
    __tablename__ = "coach_inquiries"

    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(sa.Uuid, index=True)
    application_id: Mapped[UUID | None] = mapped_column(sa.Uuid, nullable=True)
    # resume_workspace / capacity_gate / coach_page / weekly_action
    source_screen: Mapped[str] = mapped_column(String(64))
    contact_method: Mapped[str] = mapped_column(String(128))  # 微信号/手机/email
    status: Mapped[CoachInquiryStatus] = mapped_column(
        sa.Enum(CoachInquiryStatus, name="coach_inquiry_status_enum"),
        default=CoachInquiryStatus.NEW,
    )
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa.func.now(), index=True
    )
