from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from src.models.resource_item import ResourceType


class CreateResourceIn(BaseModel):
    type: ResourceType = ResourceType.OTHER
    title: str
    content_text: str = ""
    source_url: str | None = None
    tags: list[str] = Field(default_factory=list)


class UpdateResourceIn(BaseModel):
    type: ResourceType | None = None
    title: str | None = None
    content_text: str | None = None
    source_url: str | None = None
    tags: list[str] | None = None


class ResourceOut(BaseModel):
    id: UUID
    type: ResourceType
    title: str
    content_text: str
    source_url: str | None
    tags: list[str]
    ai_summary: str
    ai_extracted_signals: list[dict[str, object]]
    linked_company_names: list[str]
    created_at: datetime


class ResourceList(BaseModel):
    items: list[ResourceOut]
    total: int


class CollectionIn(BaseModel):
    name: str
    description: str = ""


class CollectionOut(BaseModel):
    id: UUID
    name: str
    description: str
    created_at: datetime
    item_count: int
