from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.db import Base

if TYPE_CHECKING:
    from src.models.master_resume import MasterResume


class AbilityCard(Base):
    __tablename__ = "ability_cards"

    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid4)
    master_resume_id: Mapped[UUID] = mapped_column(
        sa.Uuid, ForeignKey("master_resumes.id"), index=True
    )
    skill_name: Mapped[str] = mapped_column(String(128))
    evidence_text: Mapped[str] = mapped_column(String(2048), default="")
    level: Mapped[int] = mapped_column(Integer, default=3)  # 1-5
    last_used_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_weak: Mapped[bool] = mapped_column(Boolean, default=False)
    resume: Mapped["MasterResume"] = relationship(back_populates="ability_cards")


class ProjectCard(Base):
    __tablename__ = "project_cards"

    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid4)
    master_resume_id: Mapped[UUID] = mapped_column(
        sa.Uuid, ForeignKey("master_resumes.id"), index=True
    )
    project_name: Mapped[str] = mapped_column(String(256))
    role: Mapped[str] = mapped_column(String(128), default="")
    period: Mapped[str] = mapped_column(String(64), default="")
    scale_data: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    star: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    tech_stack: Mapped[list[str]] = mapped_column(JSON, default=list)
    domain_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_weak: Mapped[bool] = mapped_column(Boolean, default=False)
    weak_reasons: Mapped[list[str]] = mapped_column(JSON, default=list)
    cross_domain_translation: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    resume: Mapped["MasterResume"] = relationship(back_populates="project_cards")


class ExperienceCard(Base):
    __tablename__ = "experience_cards"

    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid4)
    master_resume_id: Mapped[UUID] = mapped_column(
        sa.Uuid, ForeignKey("master_resumes.id"), index=True
    )
    company_encrypted: Mapped[str] = mapped_column(String(1024))  # 加密；明文走 service 解
    period: Mapped[str] = mapped_column(String(64), default="")
    title: Mapped[str] = mapped_column(String(128), default="")
    scope: Mapped[str] = mapped_column(String(512), default="")
    achievements: Mapped[list[str]] = mapped_column(JSON, default=list)
    industry: Mapped[str] = mapped_column(String(64), default="")
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    resume: Mapped["MasterResume"] = relationship(back_populates="experience_cards")
