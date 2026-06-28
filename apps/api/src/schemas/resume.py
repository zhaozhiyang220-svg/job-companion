from pydantic import BaseModel, Field


class AbilityIn(BaseModel):
    skill_name: str
    evidence_text: str = ""
    level: int = 3
    last_used_year: int | None = None
    tags: list[str] = Field(default_factory=list)


class STAR(BaseModel):
    situation: str = ""
    task: str = ""
    action: str = ""
    result: str = ""


class ProjectIn(BaseModel):
    project_name: str
    role: str = ""
    period: str = ""
    scale_data: dict[str, object] = Field(default_factory=dict)
    star: STAR = Field(default_factory=STAR)
    tech_stack: list[str] = Field(default_factory=list)
    domain_tags: list[str] = Field(default_factory=list)


class ExperienceIn(BaseModel):
    company: str
    period: str = ""
    title: str = ""
    scope: str = ""
    achievements: list[str] = Field(default_factory=list)
    industry: str = ""
    is_current: bool = False


class ParsedResume(BaseModel):
    basic_info: dict[str, object] = Field(default_factory=dict)
    ability_cards: list[AbilityIn] = Field(default_factory=list)
    project_cards: list[ProjectIn] = Field(default_factory=list)
    experience_cards: list[ExperienceIn] = Field(default_factory=list)
