from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class ResourceCollectionLink(Base):
    __tablename__ = "resource_collection_links"

    collection_id: Mapped[UUID] = mapped_column(
        sa.Uuid, ForeignKey("resource_collections.id"), primary_key=True
    )
    resource_id: Mapped[UUID] = mapped_column(
        sa.Uuid, ForeignKey("resource_items.id"), primary_key=True
    )
