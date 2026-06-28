from datetime import date, datetime
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy import JSON, Date, DateTime, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class WeeklyDigest(Base):
    __tablename__ = "weekly_digests"
    __table_args__ = (UniqueConstraint("user_id", "week_of", name="uq_user_week"),)

    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(sa.Uuid, index=True)
    week_of: Mapped[date] = mapped_column(Date, index=True)
    stats: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    ai_observation_text: Mapped[str] = mapped_column(Text, default="")
    suggested_actions: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa.func.now()
    )
