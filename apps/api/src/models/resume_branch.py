from datetime import datetime
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class ResumeBranch(Base):
    __tablename__ = "resume_branches"

    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid4)
    application_id: Mapped[UUID] = mapped_column(
        sa.Uuid, ForeignKey("applications.id"), index=True
    )
    version_label: Mapped[str] = mapped_column(String(16), default="v1")
    based_on_master_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa.func.now()
    )
    patch: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    # [{op_index, reason}]
    ai_reasoning: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    match_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    language: Mapped[str] = mapped_column(String(8), default="zh")
    exported_pdf_urls: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa.func.now()
    )
