from typing import Any

from pydantic import BaseModel, Field, model_validator


class _DropNone(BaseModel):
    """LLM 常对缺失的可选字段返回显式 null；Pydantic 的默认值只在 key 缺失时生效，
    显式 null 仍会因类型不符报错。这里在校验前丢弃值为 None 的键，让默认值兜底。"""

    @model_validator(mode="before")
    @classmethod
    def _drop_none(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return {k: v for k, v in data.items() if v is not None}
        return data


class AbilityIn(_DropNone):
    skill_name: str
    evidence_text: str = ""
    level: int = 3
    last_used_year: int | None = None
    tags: list[str] = Field(default_factory=list)


class STAR(_DropNone):
    situation: str = ""
    task: str = ""
    action: str = ""
    result: str = ""


class ProjectIn(_DropNone):
    project_name: str
    role: str = ""
    period: str = ""
    scale_data: dict[str, object] = Field(default_factory=dict)
    star: STAR = Field(default_factory=STAR)
    tech_stack: list[str] = Field(default_factory=list)
    domain_tags: list[str] = Field(default_factory=list)


class ExperienceIn(_DropNone):
    company: str
    period: str = ""
    title: str = ""
    scope: str = ""
    achievements: list[str] = Field(default_factory=list)
    industry: str = ""
    is_current: bool = False


class ParsedResume(_DropNone):
    basic_info: dict[str, object] = Field(default_factory=dict)
    ability_cards: list[AbilityIn] = Field(default_factory=list)
    project_cards: list[ProjectIn] = Field(default_factory=list)
    experience_cards: list[ExperienceIn] = Field(default_factory=list)
