from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class ResourceType(StrEnum):
    INTERVIEW_RECALL = "interview_recall"
    COMPANY_INTEL = "company_intel"
    RECRUITER_BG = "recruiter_bg"
    INDUSTRY_DOC = "industry_doc"
    OTHER = "other"


class ResourceItem(Base):
    __tablename__ = "resource_items"

    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(sa.Uuid, index=True)
    type: Mapped[ResourceType] = mapped_column(
        sa.Enum(ResourceType, name="resource_type_enum"),
        default=ResourceType.OTHER,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(256))
    content_text: Mapped[str] = mapped_column(Text, default="")
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    attachments: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    ai_summary: Mapped[str] = mapped_column(Text, default="")
    ai_extracted_signals: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    linked_company_names: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa.func.now()
    )
