from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.db import Base

if TYPE_CHECKING:
    from src.models.job_posting import JobPosting


class ApplicationStatus(StrEnum):
    DRAFTING = "drafting"
    ARCHIVED = "archived"
    # v2 扩展预留（枚举先建，避免后续迁移）
    APPLIED = "applied"
    INTERVIEWING = "interviewing"
    OFFERED = "offered"
    REJECTED = "rejected"


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(sa.Uuid, ForeignKey("users.id"), index=True)
    status: Mapped[ApplicationStatus] = mapped_column(
        sa.Enum(ApplicationStatus, name="application_status_enum"),
        default=ApplicationStatus.DRAFTING,
        index=True,
    )
    priority: Mapped[int] = mapped_column(Integer, default=3)  # 1-5
    notes: Mapped[str] = mapped_column(String(1024), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa.func.now()
    )
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()
    )

    job_posting: Mapped["JobPosting"] = relationship(
        back_populates="application", uselist=False, cascade="all,delete-orphan"
    )
