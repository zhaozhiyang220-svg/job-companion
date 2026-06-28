from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.db import Base

if TYPE_CHECKING:
    from src.models.cards import AbilityCard, ExperienceCard, ProjectCard


class MasterResume(Base):
    __tablename__ = "master_resumes"

    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        sa.Uuid, ForeignKey("users.id"), unique=True, index=True
    )
    basic_info: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    parsed_from_file_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    quality_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()
    )

    ability_cards: Mapped[list["AbilityCard"]] = relationship(
        back_populates="resume", cascade="all,delete-orphan"
    )
    project_cards: Mapped[list["ProjectCard"]] = relationship(
        back_populates="resume", cascade="all,delete-orphan"
    )
    experience_cards: Mapped[list["ExperienceCard"]] = relationship(
        back_populates="resume", cascade="all,delete-orphan"
    )
