from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class ApplicationResourceLink(Base):
    __tablename__ = "application_resource_links"

    application_id: Mapped[UUID] = mapped_column(
        sa.Uuid, ForeignKey("applications.id"), primary_key=True
    )
    # FK resource_item_id → resource_items.id 在 Plan 4 创建 ResourceItem 后补约束
    resource_item_id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True)
