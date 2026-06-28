from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.models.application import ApplicationStatus


class CreateApplicationIn(BaseModel):
    raw_text: str
    source_url: str | None = None


class UpdateApplicationIn(BaseModel):
    status: ApplicationStatus | None = None
    priority: int | None = None
    notes: str | None = None


class JobPostingOut(BaseModel):
    company_name: str
    job_title: str
    department: str
    salary_range: str
    location: str
    language: str
    requirements_parsed: dict[str, object]
    hidden_preferences: list[str]
    red_flags: list[str]
    raw_text: str
    source_url: str | None


class ApplicationOut(BaseModel):
    id: UUID
    status: ApplicationStatus
    priority: int
    notes: str
    created_at: datetime
    last_active_at: datetime
    job_posting: JobPostingOut


class ApplicationListItem(BaseModel):
    id: UUID
    status: ApplicationStatus
    company_name: str
    job_title: str
    department: str
    salary_range: str
    last_active_at: datetime


class ApplicationList(BaseModel):
    items: list[ApplicationListItem]
    total: int
    page: int
    page_size: int
