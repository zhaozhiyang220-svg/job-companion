from pydantic import BaseModel, Field


class JDRequirements(BaseModel):
    hard: list[str] = Field(default_factory=list)
    soft: list[str] = Field(default_factory=list)
    years: str = ""


class ParsedJD(BaseModel):
    company_name: str = ""
    job_title: str = ""
    department: str = ""
    salary_range: str = ""
    location: str = ""
    language: str = "zh"
    requirements: JDRequirements = Field(default_factory=JDRequirements)
    hidden_preferences: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
