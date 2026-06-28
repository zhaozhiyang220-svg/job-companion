from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class PersonaType(StrEnum):
    FRESH_GRAD = "fresh_grad"
    JOB_HOPPER = "job_hopper"
    CAREER_CHANGER = "career_changer"


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid4)
    email_encrypted: Mapped[str | None] = mapped_column(String(512), nullable=True)
    email_lookup_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True, index=True
    )
    wechat_openid: Mapped[str | None] = mapped_column(
        String(128), nullable=True, unique=True, index=True
    )
    nickname: Mapped[str | None] = mapped_column(String(128), nullable=True)
    persona_type: Mapped[PersonaType | None] = mapped_column(
        sa.Enum(PersonaType, name="persona_type_enum"), nullable=True
    )
    preferences: Mapped[dict[str, object]] = mapped_column(sa.JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa.func.now()
    )
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
