from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UploadInitIn(BaseModel):
    filename: str
    content_type: str


class UploadInitOut(BaseModel):
    upload_url: str
    s3_key: str


class ParseIn(BaseModel):
    s3_key: str


class AbilityCardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    skill_name: str
    evidence_text: str
    level: int
    last_used_year: int | None
    tags: list[str]
    is_weak: bool


class ProjectCardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_name: str
    role: str
    period: str
    scale_data: dict[str, object]
    star: dict[str, object]
    tech_stack: list[str]
    domain_tags: list[str]
    is_weak: bool
    weak_reasons: list[str]
    cross_domain_translation: dict[str, object]


class ExperienceCardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company: str
    period: str
    title: str
    scope: str
    achievements: list[str]
    industry: str
    is_current: bool


class MasterResumeOut(BaseModel):
    id: UUID
    basic_info: dict[str, object]
    quality_score: int | None
    ability_cards: list[AbilityCardOut]
    project_cards: list[ProjectCardOut]
    experience_cards: list[ExperienceCardOut]
