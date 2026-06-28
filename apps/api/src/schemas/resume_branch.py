from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CreateBranchIn(BaseModel):
    language: str | None = None  # 默认跟随 JD 的 language


class UpdateBranchIn(BaseModel):
    patch: list[dict[str, object]]


class BranchSummary(BaseModel):
    id: UUID
    version_label: str
    match_score: int | None
    language: str
    created_at: datetime
    is_active: bool


class BranchDetail(BranchSummary):
    patch: list[dict[str, object]]
    ai_reasoning: list[dict[str, object]]
    rendered_resume: dict[str, object]  # apply_operations 结果
    master_snapshot: dict[str, object]  # 同时返回 master 便于 diff 渲染
