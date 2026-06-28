# Plan 3：ResumeBranch + PatchOperations 模块 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 单机会内"简历定制"模块完整可用——基于主简历 + JD 解读 → AI 生成补丁分支（PatchOperations）→ 并排 diff 视图 + 修改理由透明 → 中英 PDF 导出（现公司默认脱敏）→ Coach 导流入口。

**Architecture:** PatchOperation DSL（reorder / emphasize / rewrite / hide / insert_keyword）— 不存全量快照，只存操作序列；apply(master, ops) 函数纯逻辑产出渲染版本；评分 + 修改幅度 guard；WeasyPrint 把 HTML 模板渲染为 PDF。

**Tech Stack:** WeasyPrint 60+ / Jinja2 3.1 / 复用 Plan 0-2 全部栈；MiniMax Context Caching（MiniMax-M1 长 system prompt + 主简历缓存）

## Global Constraints
- 继承前序所有约束
- PatchOperations 必须可序列化为 JSON
- 单 field 改写幅度 ≤ 30% 字数（hard guard 在 apply 时校验）
- 所有补丁修改必须有对应 `ai_reasoning` 条目，UI 必须展示
- 导出 PDF 默认对 `is_current=true` 经历卡的 company 字段脱敏为「某知名互联网公司 / Major Tech Company」
- 中文 PDF 字体：思源宋体/黑体 fallback；英文 PDF 字体：Inter/Helvetica

---

## Task 1: PatchOperation DSL + Apply Function

**Files:**
- Create: `apps/api/src/services/patch_ops.py`
- Create: `apps/api/tests/test_patch_ops.py`

**Interfaces:**
- Produces:
  - `Operation = ReorderOp | EmphasizeOp | RewriteOp | HideOp | InsertKeywordOp`（discriminated union）
  - `apply_operations(master: dict, ops: list[dict]) -> dict` → 渲染版本（card 列表保留原始 id，新增 `_hidden / _emphasized / _patched_field` 标记）
  - `validate_rewrite_intensity(original: str, new: str, max_pct: float = 0.30) -> bool`

- [ ] **Step 1：写 service**

`apps/api/src/services/patch_ops.py`：
```python
from typing import Literal, TypedDict, Union, cast
from difflib import SequenceMatcher

class ReorderOp(TypedDict):
    type: Literal["reorder"]
    card_id: str
    new_position: int

class EmphasizeOp(TypedDict):
    type: Literal["emphasize"]
    card_id: str
    intensity: Literal["low", "medium", "high"]

class RewriteOp(TypedDict):
    type: Literal["rewrite"]
    card_id: str
    field: str
    new_text: str

class HideOp(TypedDict):
    type: Literal["hide"]
    card_id: str

class InsertKeywordOp(TypedDict):
    type: Literal["insert_keyword"]
    card_id: str
    keywords: list[str]

Operation = Union[ReorderOp, EmphasizeOp, RewriteOp, HideOp, InsertKeywordOp]

VALID_TYPES = {"reorder", "emphasize", "rewrite", "hide", "insert_keyword"}

class RewriteTooLargeError(ValueError):
    """单字段改写超过 30% 字数上限"""

def validate_rewrite_intensity(original: str, new: str, max_pct: float = 0.30) -> bool:
    if not original:
        return True
    ratio = SequenceMatcher(None, original, new).ratio()
    return (1 - ratio) <= max_pct

def apply_operations(master: dict, ops: list[dict]) -> dict:
    """将 ops 应用到 master 副本上。
    master shape: {ability_cards: [...], project_cards: [...], experience_cards: [...]}
    """
    import copy
    result = copy.deepcopy(master)
    # 索引：id → (collection_name, idx)
    index: dict[str, tuple[str, int]] = {}
    for coll in ("ability_cards", "project_cards", "experience_cards"):
        for i, c in enumerate(result.get(coll, [])):
            cid = str(c.get("id"))
            index[cid] = (coll, i)
            c.setdefault("_emphasized", "none")
            c.setdefault("_hidden", False)
            c.setdefault("_patched_fields", [])
            c.setdefault("_inserted_keywords", [])

    for raw in ops:
        op = cast(Operation, raw)
        t = op["type"]
        if t not in VALID_TYPES:
            raise ValueError(f"unknown op type: {t}")
        cid = op["card_id"]
        if cid not in index:
            continue  # silently skip unknown card
        coll, idx = index[cid]
        card = result[coll][idx]
        if t == "hide":
            card["_hidden"] = True
        elif t == "emphasize":
            card["_emphasized"] = op["intensity"]
        elif t == "rewrite":
            field = op["field"]
            original = str(card.get(field, "")) if not isinstance(card.get(field), dict) else \
                       str(card.get(field, {}).get("result", "")) if field == "star.result" else ""
            if not validate_rewrite_intensity(original, op["new_text"]):
                raise RewriteTooLargeError(f"rewrite of {cid}.{field} exceeds 30% threshold")
            # 支持 star.field 嵌套
            if "." in field:
                top, sub = field.split(".", 1)
                card.setdefault(top, {})[sub] = op["new_text"]
            else:
                card[field] = op["new_text"]
            card["_patched_fields"].append(field)
        elif t == "insert_keyword":
            card["_inserted_keywords"].extend(op["keywords"])
        elif t == "reorder":
            # 移到 collection 内的 new_position（同 collection 内重排）
            old = result[coll].pop(idx)
            new_pos = max(0, min(op["new_position"], len(result[coll])))
            result[coll].insert(new_pos, old)
            # 重建 index
            for i2, c2 in enumerate(result[coll]):
                index[str(c2["id"])] = (coll, i2)

    # 过滤 _hidden（导出渲染时再决定，本函数保留全量但标记）
    return result
```

- [ ] **Step 2：测试**

`apps/api/tests/test_patch_ops.py`：
```python
import pytest
from src.services.patch_ops import apply_operations, validate_rewrite_intensity, RewriteTooLargeError

MASTER = {
  "ability_cards": [{"id":"a1","skill_name":"增长","level":3}],
  "project_cards": [{"id":"p1","project_name":"拉新", "star":{"situation":"","task":"","action":"","result":"原结果"}}],
  "experience_cards": [{"id":"e1","company":"字节","title":"PM"},{"id":"e2","company":"美团","title":"PM"}],
}

def test_emphasize_marks_card():
    r = apply_operations(MASTER, [{"type":"emphasize","card_id":"a1","intensity":"high"}])
    assert r["ability_cards"][0]["_emphasized"] == "high"

def test_hide_marks_card():
    r = apply_operations(MASTER, [{"type":"hide","card_id":"e2"}])
    e2 = next(c for c in r["experience_cards"] if c["id"] == "e2")
    assert e2["_hidden"] is True

def test_rewrite_within_threshold():
    r = apply_operations(MASTER, [{"type":"rewrite","card_id":"p1","field":"star.result","new_text":"原结果，并补充数据"}])
    assert "数据" in r["project_cards"][0]["star"]["result"]

def test_rewrite_too_large_raises():
    with pytest.raises(RewriteTooLargeError):
        apply_operations(MASTER, [{"type":"rewrite","card_id":"a1","field":"skill_name","new_text":"完全不同的能力名字写很长很长很长"}])

def test_reorder_moves_card():
    r = apply_operations(MASTER, [{"type":"reorder","card_id":"e2","new_position":0}])
    assert r["experience_cards"][0]["id"] == "e2"

def test_insert_keyword_appends():
    r = apply_operations(MASTER, [{"type":"insert_keyword","card_id":"a1","keywords":["数据","B2C"]}])
    assert r["ability_cards"][0]["_inserted_keywords"] == ["数据","B2C"]

def test_unknown_card_skipped():
    r = apply_operations(MASTER, [{"type":"hide","card_id":"nonexistent"}])
    assert r["ability_cards"][0]["_hidden"] is False

def test_validate_rewrite_intensity():
    assert validate_rewrite_intensity("hello world", "hello world!") is True
    assert validate_rewrite_intensity("hello world", "totally different text") is False
```

Run: `pytest -q tests/test_patch_ops.py` → 8 passed

- [ ] **Step 3：提交**

```bash
git add apps/api && git commit -m "feat(api): PatchOperation DSL with apply + rewrite intensity guard"
```

---

## Task 2: ResumeBranch 模型 + 迁移

**Files:**
- Create: `apps/api/src/models/resume_branch.py`
- Create: `apps/api/alembic/versions/0008_resume_branch.py`
- Modify: `apps/api/src/models/__init__.py`
- Create: `apps/api/tests/test_resume_branch_model.py`

**Interfaces:**
- Produces:
  - `ResumeBranch(id, application_id, version_label, based_on_master_at, patch JSON, ai_reasoning JSON, match_score, language, exported_pdf_urls JSON, is_active, created_at)`

- [ ] **Step 1：模型**

```python
from datetime import datetime
from uuid import uuid4, UUID
import sqlalchemy as sa
from sqlalchemy import String, DateTime, JSON, ForeignKey, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.db import Base

class ResumeBranch(Base):
    __tablename__ = "resume_branches"
    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid4)
    application_id: Mapped[UUID] = mapped_column(sa.Uuid, ForeignKey("applications.id"), index=True)
    version_label: Mapped[str] = mapped_column(String(16), default="v1")
    based_on_master_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=sa.func.now())
    patch: Mapped[list] = mapped_column(JSON, default=list)
    ai_reasoning: Mapped[list] = mapped_column(JSON, default=list)  # [{card_id, op_index, reason}]
    match_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    language: Mapped[str] = mapped_column(String(8), default="zh")
    exported_pdf_urls: Mapped[list] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=sa.func.now())
```

`__init__.py` 追加：`from src.models.resume_branch import ResumeBranch  # noqa`

- [ ] **Step 2：迁移 + 测试**

```bash
cd apps/api && source .venv/bin/activate
alembic revision --autogenerate -m "resume branch"
alembic upgrade head
```

`tests/test_resume_branch_model.py`：
```python
from src.models import User, Application, JobPosting, ResumeBranch

def test_create_branch(db):
    u = User(preferences={}); db.add(u); db.flush()
    a = Application(user_id=u.id); a.job_posting = JobPosting(raw_text="x")
    db.add(a); db.flush()
    b = ResumeBranch(application_id=a.id, version_label="v1",
                     patch=[{"type":"hide","card_id":"x"}],
                     ai_reasoning=[{"op_index":0,"reason":"无关岗位"}],
                     match_score=72, language="zh")
    db.add(b); db.flush()
    assert b.match_score == 72
    assert b.patch[0]["type"] == "hide"
```

Run: PASS

- [ ] **Step 3：提交**

```bash
cd ../.. && git add apps/api && git commit -m "feat(api): ResumeBranch model with PatchOperations + ai_reasoning"
```

---

## Task 3: AI 补丁生成 Service（含 Prompt Caching）

**Files:**
- Create: `apps/api/src/ai/prompts/generate_patch.py`
- Create: `apps/api/src/services/patch_generator.py`
- Create: `apps/api/tests/test_patch_generator.py`

**Interfaces:**
- Produces:
  - `async generate_patch(master_serialized: dict, jd_serialized: dict, language: str, user_id: UUID) -> {patch: [Operation], reasoning: [{op_index, reason}]}`
  - MiniMax Context Caching：master_serialized 部分作为 cached prefix（命中后缓存部分按 1/3 价计费，整体补丁生成成本降 ~70%）

- [ ] **Step 1：prompt**

```python
GENERATE_PATCH_SYSTEM = """你是一位资深简历教练。任务：基于「主简历」和「目标 JD」，生成一组 PatchOperations 把主简历"调整为更匹配 JD 的版本"。

PatchOperation 类型（严格使用，不许新增）：
- {"type":"reorder","card_id":str,"new_position":int}
- {"type":"emphasize","card_id":str,"intensity":"low|medium|high"}
- {"type":"rewrite","card_id":str,"field":str,"new_text":str}
- {"type":"hide","card_id":str}
- {"type":"insert_keyword","card_id":str,"keywords":[str]}

约束：
- rewrite 改写幅度 ≤ 30%（保留原意，只调措辞）
- 每个 op 必须对应一条 reasoning（解释为什么）
- 不要删主版本里的"硬核能力"——只 hide 与岗位无关项
- 输出语言 = JD 的 language

输出严格 JSON：
{"patch":[...], "reasoning":[{"op_index":0,"reason":str}, ...]}
仅 JSON。
"""
```

- [ ] **Step 2：service（启用 MiniMax Context Caching）**

```python
import json
from uuid import UUID
from src.ai.llm_client import LLMClient
from src.ai.prompts.generate_patch import GENERATE_PATCH_SYSTEM
from src.core.cache import minimax_cache_store      # Redis store: user_id -> minimax cache_id (TTL 300s)

_llm = LLMClient()

async def generate_patch(master_serialized: dict, jd_serialized: dict, language: str, user_id: UUID) -> dict:
    # MiniMax Context Caching：把 master 序列化作为缓存前缀，5 分钟内同一用户为多个 JD 生成补丁可复用
    # 实现：首次调用 LLMClient 后取 X-Cache-Id 落 Redis；后续调用通过 extra_body={"cache_id": ...} 复用
    cache_id = await minimax_cache_store.get(user_id)

    msg_user = {
        "role": "user",
        # MiniMax 当前 chat completion 走单字符串 content；缓存通过 cache_id 关联，不通过 cache_control 字段
        "content": json.dumps(
            {"master": master_serialized, "jd": jd_serialized, "output_language": language},
            ensure_ascii=False,
        ),
    }

    raw, new_cache_id = await _llm.acomplete(
        model="auto-m1",
        system=GENERATE_PATCH_SYSTEM,
        messages=[msg_user],
        max_tokens=2048, user_id=user_id, scene="patch_generate",
        extra_body={"cache_id": cache_id} if cache_id else None,
    )
    if new_cache_id and not cache_id:
        await minimax_cache_store.set(user_id, new_cache_id, ttl_sec=300)

    data = json.loads(raw)
    if "patch" not in data or "reasoning" not in data:
        raise ValueError("invalid patch generator response")
    return data
```

> **注**：MiniMax Context Caching 的 token / API 字段以官方文档为准；若 LiteLLM 版本暂未透传 `extra_body`，可改用直接 `httpx.AsyncClient` + `api_base=settings.minimax_api_base`，缓存层在 `LLMClient` 内部统一封装。

- [ ] **Step 3：测试**

```python
import json
from unittest.mock import patch, AsyncMock
from uuid import uuid4
import pytest
from src.services.patch_generator import generate_patch

@pytest.mark.asyncio
async def test_generate_patch():
    fake = {"patch":[{"type":"emphasize","card_id":"a1","intensity":"high"}],
            "reasoning":[{"op_index":0,"reason":"JD 强调此能力"}]}
    with patch("src.services.patch_generator._llm.acomplete", AsyncMock(return_value=json.dumps(fake))):
        out = await generate_patch({"ability_cards":[{"id":"a1","skill_name":"增长"}]},
                                    {"company_name":"字节","requirements":{"hard":["增长"]}},
                                    "zh", uuid4())
    assert out["patch"][0]["intensity"] == "high"
    assert "JD 强调" in out["reasoning"][0]["reason"]
```

Run: PASS

- [ ] **Step 4：提交**

```bash
git add apps/api && git commit -m "feat(api): AI patch generator (MiniMax-M1) with Context Caching on master resume"
```

---

## Task 4: AI 评分 Service

**Files:**
- Create: `apps/api/src/ai/prompts/score_resume.py`
- Create: `apps/api/src/services/resume_scorer.py`
- Create: `apps/api/tests/test_resume_scorer.py`

**Interfaces:**
- Produces:
  - `async score_branch(rendered: dict, jd: dict, user_id: UUID) -> int` (0-100)

- [ ] **Step 1：prompt**

```python
SCORE_RESUME_SYSTEM = """你是面试官，给"针对 JD 的简历版本"打 0-100 分。
评分维度：硬技能匹配 40 / 经验相关 30 / 项目数据 20 / 表述清晰 10。
输入：rendered_resume + jd。
输出严格 JSON：{"score": int}
仅 JSON。
"""
```

- [ ] **Step 2：service**

```python
import json
from uuid import UUID
from src.ai.llm_client import LLMClient
from src.ai.prompts.score_resume import SCORE_RESUME_SYSTEM

_llm = LLMClient()

async def score_branch(rendered: dict, jd: dict, user_id: UUID) -> int:
    raw = await _llm.acomplete(
        model="auto-light",
        system=SCORE_RESUME_SYSTEM,
        messages=[{"role":"user","content": json.dumps({"resume":rendered, "jd":jd}, ensure_ascii=False)}],
        max_tokens=128, user_id=user_id, scene="resume_score",
    )
    return int(json.loads(raw)["score"])
```

- [ ] **Step 3：测试**

```python
import json
from unittest.mock import patch, AsyncMock
from uuid import uuid4
import pytest
from src.services.resume_scorer import score_branch

@pytest.mark.asyncio
async def test_score_returns_int():
    with patch("src.services.resume_scorer._llm.acomplete", AsyncMock(return_value=json.dumps({"score": 82}))):
        s = await score_branch({}, {}, uuid4())
    assert s == 82
```

Run: PASS

- [ ] **Step 4：提交**

```bash
git add apps/api && git commit -m "feat(api): resume scorer (abab6.5s-chat) 0-100 against JD"
```

---

## Task 5: API — ResumeBranch CRUD + Generate + Rollback Endpoints

**Files:**
- Create: `apps/api/src/routers/resume_branch.py`
- Create: `apps/api/src/schemas/resume_branch.py`
- Modify: `apps/api/src/main.py`
- Create: `apps/api/tests/test_resume_branch_api.py`

**Interfaces:**
- Produces:
  - `POST /api/v1/applications/{app_id}/branches` body `{language?}` → AI 生成补丁 + 评分，返回新 branch
  - `GET /api/v1/applications/{app_id}/branches` → 该机会下所有分支
  - `GET /api/v1/applications/{app_id}/branches/{branch_id}` → 单分支详情（含 rendered_resume）
  - `PATCH /api/v1/applications/{app_id}/branches/{branch_id}` body `{patch_operations: [...]}` → 手动覆盖 ops
  - `DELETE /api/v1/applications/{app_id}/branches/{branch_id}` → 删除
  - `POST /api/v1/applications/{app_id}/branches/{branch_id}/rollback-to/{prev_id}` → 把目标分支的 ops 复制为新版本

- [ ] **Step 1：schema**

```python
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

class CreateBranchIn(BaseModel):
    language: str | None = None  # 默认跟随 JD 的 language

class UpdateBranchIn(BaseModel):
    patch: list[dict]

class BranchSummary(BaseModel):
    id: UUID; version_label: str; match_score: int | None
    language: str; created_at: datetime; is_active: bool

class BranchDetail(BranchSummary):
    patch: list[dict]; ai_reasoning: list[dict]
    rendered_resume: dict   # apply_operations 结果
    master_snapshot: dict   # 同时返回 master 便于 diff 渲染
```

- [ ] **Step 2：router**

`apps/api/src/routers/resume_branch.py`：
```python
from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
from src.core.db import get_db
from src.core.deps import current_user
from src.core.security import decrypt_field
from src.models import User, Application, MasterResume, ResumeBranch
from src.services.patch_generator import generate_patch
from src.services.patch_ops import apply_operations, RewriteTooLargeError
from src.services.resume_scorer import score_branch
from src.schemas.resume_branch import CreateBranchIn, UpdateBranchIn, BranchSummary, BranchDetail

router = APIRouter(prefix="/api/v1/applications/{app_id}/branches", tags=["resume-branch"])

def _serialize_master(r: MasterResume) -> dict:
    return {
        "ability_cards": [{
            "id": str(c.id), "skill_name": c.skill_name, "evidence_text": c.evidence_text,
            "level": c.level, "last_used_year": c.last_used_year, "tags": c.tags,
        } for c in r.ability_cards],
        "project_cards": [{
            "id": str(c.id), "project_name": c.project_name, "role": c.role, "period": c.period,
            "scale_data": c.scale_data, "star": c.star, "tech_stack": c.tech_stack,
            "domain_tags": c.domain_tags,
        } for c in r.project_cards],
        "experience_cards": [{
            "id": str(c.id), "company": decrypt_field(c.company_encrypted) if c.company_encrypted else "",
            "period": c.period, "title": c.title, "scope": c.scope,
            "achievements": c.achievements, "industry": c.industry, "is_current": c.is_current,
        } for c in r.experience_cards],
    }

def _serialize_jd(app: Application) -> dict:
    jp = app.job_posting
    return {
        "company_name": jp.company_name, "job_title": jp.job_title,
        "salary_range": jp.salary_range, "location": jp.location,
        "language": jp.language, "requirements": jp.requirements_parsed,
        "hidden_preferences": jp.hidden_preferences,
    }

def _get_app(app_id: UUID, user: User, db: Session) -> Application:
    a = db.query(Application).filter(Application.id == app_id, Application.user_id == user.id) \
         .options(selectinload(Application.job_posting)).first()
    if not a: raise HTTPException(404, "application not found")
    return a

def _get_master(user: User, db: Session) -> MasterResume:
    r = db.query(MasterResume).filter(MasterResume.user_id == user.id).first()
    if not r: raise HTTPException(404, "master resume not found; upload first")
    return r

def _next_version(db: Session, app_id: UUID) -> str:
    n = db.query(ResumeBranch).filter(ResumeBranch.application_id == app_id).count()
    return f"v{n+1}"

@router.post("", response_model=BranchDetail, status_code=201)
async def create_branch(app_id: UUID, body: CreateBranchIn, user: User = Depends(current_user), db: Session = Depends(get_db)) -> BranchDetail:
    app = _get_app(app_id, user, db)
    r = _get_master(user, db)
    master = _serialize_master(r)
    jd = _serialize_jd(app)
    lang = body.language or jd.get("language", "zh")
    out = await generate_patch(master, jd, lang, user.id)
    try:
        rendered = apply_operations(master, out["patch"])
    except RewriteTooLargeError as e:
        raise HTTPException(422, str(e))
    score = await score_branch(rendered, jd, user.id)

    # 旧分支 is_active = False
    for old in db.query(ResumeBranch).filter(ResumeBranch.application_id == app_id, ResumeBranch.is_active == True).all():
        old.is_active = False

    b = ResumeBranch(
        application_id=app_id, version_label=_next_version(db, app_id),
        patch=out["patch"], ai_reasoning=out["reasoning"], match_score=score,
        language=lang, is_active=True,
    )
    db.add(b); db.commit(); db.refresh(b)
    return BranchDetail(
        id=b.id, version_label=b.version_label, match_score=b.match_score, language=b.language,
        created_at=b.created_at, is_active=b.is_active, patch=b.patch, ai_reasoning=b.ai_reasoning,
        rendered_resume=rendered, master_snapshot=master,
    )

@router.get("", response_model=list[BranchSummary])
def list_branches(app_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[BranchSummary]:
    _get_app(app_id, user, db)
    bs = db.query(ResumeBranch).filter(ResumeBranch.application_id == app_id).order_by(ResumeBranch.created_at.desc()).all()
    return [BranchSummary(id=b.id, version_label=b.version_label, match_score=b.match_score,
                          language=b.language, created_at=b.created_at, is_active=b.is_active) for b in bs]

@router.get("/{branch_id}", response_model=BranchDetail)
def get_branch(app_id: UUID, branch_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> BranchDetail:
    _get_app(app_id, user, db)
    b = db.query(ResumeBranch).filter(ResumeBranch.id == branch_id, ResumeBranch.application_id == app_id).first()
    if not b: raise HTTPException(404, "branch not found")
    r = _get_master(user, db)
    master = _serialize_master(r)
    rendered = apply_operations(master, b.patch)
    return BranchDetail(id=b.id, version_label=b.version_label, match_score=b.match_score,
                        language=b.language, created_at=b.created_at, is_active=b.is_active,
                        patch=b.patch, ai_reasoning=b.ai_reasoning,
                        rendered_resume=rendered, master_snapshot=master)

@router.patch("/{branch_id}", response_model=BranchDetail)
def update_branch(app_id: UUID, branch_id: UUID, body: UpdateBranchIn, user: User = Depends(current_user), db: Session = Depends(get_db)) -> BranchDetail:
    _get_app(app_id, user, db)
    b = db.query(ResumeBranch).filter(ResumeBranch.id == branch_id, ResumeBranch.application_id == app_id).first()
    if not b: raise HTTPException(404, "not found")
    r = _get_master(user, db)
    master = _serialize_master(r)
    try:
        rendered = apply_operations(master, body.patch)
    except RewriteTooLargeError as e:
        raise HTTPException(422, str(e))
    b.patch = body.patch
    db.commit(); db.refresh(b)
    return BranchDetail(id=b.id, version_label=b.version_label, match_score=b.match_score,
                        language=b.language, created_at=b.created_at, is_active=b.is_active,
                        patch=b.patch, ai_reasoning=b.ai_reasoning,
                        rendered_resume=rendered, master_snapshot=master)

@router.delete("/{branch_id}", status_code=204)
def delete_branch(app_id: UUID, branch_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> None:
    _get_app(app_id, user, db)
    b = db.query(ResumeBranch).filter(ResumeBranch.id == branch_id, ResumeBranch.application_id == app_id).first()
    if not b: raise HTTPException(404, "not found")
    db.delete(b); db.commit()

@router.post("/{branch_id}/rollback-to/{prev_id}", response_model=BranchDetail)
def rollback_to(app_id: UUID, branch_id: UUID, prev_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> BranchDetail:
    _get_app(app_id, user, db)
    prev = db.query(ResumeBranch).filter(ResumeBranch.id == prev_id, ResumeBranch.application_id == app_id).first()
    if not prev: raise HTTPException(404, "prev branch not found")
    # 当前活跃改为新版本，复制 prev ops
    for old in db.query(ResumeBranch).filter(ResumeBranch.application_id == app_id, ResumeBranch.is_active == True).all():
        old.is_active = False
    new = ResumeBranch(
        application_id=app_id, version_label=_next_version(db, app_id),
        patch=prev.patch, ai_reasoning=[{"op_index":-1,"reason":f"回滚自 {prev.version_label}"}],
        match_score=prev.match_score, language=prev.language, is_active=True,
    )
    db.add(new); db.commit(); db.refresh(new)
    r = _get_master(user, db)
    master = _serialize_master(r)
    return BranchDetail(id=new.id, version_label=new.version_label, match_score=new.match_score,
                        language=new.language, created_at=new.created_at, is_active=new.is_active,
                        patch=new.patch, ai_reasoning=new.ai_reasoning,
                        rendered_resume=apply_operations(master, new.patch), master_snapshot=master)
```

Modify `main.py` 加入 router。

- [ ] **Step 3：测试**

`apps/api/tests/test_resume_branch_api.py`：
```python
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from src.main import app
from src.core.security import issue_session_token, encrypt_field
from src.core.db import SessionLocal
from src.models import User, MasterResume, AbilityCard, Application, JobPosting

def _setup():
    db = SessionLocal()
    u = User(preferences={}); db.add(u); db.commit(); db.refresh(u)
    r = MasterResume(user_id=u.id); db.add(r); db.flush()
    a_card = AbilityCard(master_resume_id=r.id, skill_name="增长"); db.add(a_card); db.flush()
    appl = Application(user_id=u.id); appl.job_posting = JobPosting(raw_text="...", company_name="字节", language="zh")
    db.add(appl); db.commit(); db.refresh(appl); db.refresh(a_card)
    c = TestClient(app); c.cookies.set("jc_session", issue_session_token(u.id))
    return c, str(appl.id), str(a_card.id)

def test_create_branch_generates_patch_and_score():
    c, app_id, a_id = _setup()
    fake_patch = {"patch":[{"type":"emphasize","card_id":a_id,"intensity":"high"}],
                  "reasoning":[{"op_index":0,"reason":"JD 强调增长"}]}
    with patch("src.routers.resume_branch.generate_patch", AsyncMock(return_value=fake_patch)), \
         patch("src.routers.resume_branch.score_branch", AsyncMock(return_value=82)):
        r = c.post(f"/api/v1/applications/{app_id}/branches", json={})
    assert r.status_code == 201
    b = r.json()
    assert b["match_score"] == 82
    assert b["version_label"] == "v1"
    assert b["rendered_resume"]["ability_cards"][0]["_emphasized"] == "high"
```

Run: PASS

- [ ] **Step 4：提交**

```bash
cd ../.. && git add apps/api && git commit -m "feat(api): resume branch endpoints (create/list/get/patch/delete/rollback)"
```

---

## Task 6: 中英 HTML 简历模板

**Files:**
- Create: `apps/api/src/templates/resume/base.css`
- Create: `apps/api/src/templates/resume/zh_simple.html`
- Create: `apps/api/src/templates/resume/en_simple.html`
- Create: `apps/api/src/services/template_renderer.py`
- Create: `apps/api/tests/test_template_renderer.py`

**Interfaces:**
- Produces:
  - `render_html(rendered_resume: dict, language: str, mask_current_company: bool) -> str`
  - 模板根据 `_hidden` 跳过、按 `_emphasized` 加粗/底色、按 `_inserted_keywords` 在尾部加 tag

- [ ] **Step 1：装 Jinja2 + WeasyPrint（WeasyPrint 在 Task 7）**

```bash
cd apps/api && source .venv/bin/activate
pip install jinja2==3.1.4
```
`pyproject.toml` 追加：`"jinja2==3.1.4",`

- [ ] **Step 2：写 base.css**

`apps/api/src/templates/resume/base.css`：
```css
@page { size: A4; margin: 18mm 16mm; }
body { font-family: "Noto Sans CJK SC","Noto Sans","Helvetica","Inter","Arial",sans-serif; font-size: 10.5pt; color: #222; line-height: 1.45; }
h1 { font-size: 18pt; margin: 0 0 4mm; }
h2 { font-size: 12pt; margin: 6mm 0 2mm; border-bottom: 1px solid #999; padding-bottom: 1mm; }
.basic { color: #555; font-size: 9.5pt; margin-bottom: 4mm; }
.card { margin-bottom: 4mm; }
.card.em-high { background: #fff5d6; padding: 2mm; border-left: 3px solid #f0a500; }
.card.em-medium { background: #fff9e8; padding: 1mm; }
.title { font-weight: bold; }
.meta { color: #777; font-size: 9.5pt; }
.kw { display: inline-block; background: #e6f4ff; color: #006fcc; padding: 0.5mm 2mm; margin-right: 2mm; border-radius: 2mm; font-size: 9pt; }
ul { margin: 1mm 0 0 4mm; padding: 0; }
li { margin-bottom: 1mm; }
```

- [ ] **Step 3：zh 模板**

`apps/api/src/templates/resume/zh_simple.html`：
```html
<!doctype html>
<html lang="zh">
<head><meta charset="utf-8"><style>{{ css }}</style></head>
<body>
  <h1>{{ basic.name or "" }}</h1>
  <div class="basic">
    {% if basic.phone %}{{ basic.phone }} · {% endif %}
    {% if basic.email %}{{ basic.email }} · {% endif %}
    {{ basic.location or "" }}
  </div>

  {% if experiences %}<h2>工作经历</h2>
  {% for e in experiences %}
    <div class="card em-{{ e._emphasized or 'none' }}">
      <div class="title">{{ e.company_display }} — {{ e.title }}</div>
      <div class="meta">{{ e.period }} · {{ e.industry or "" }}</div>
      {% if e.scope %}<div>{{ e.scope }}</div>{% endif %}
      {% if e.achievements %}<ul>{% for a in e.achievements %}<li>{{ a }}</li>{% endfor %}</ul>{% endif %}
      {% if e._inserted_keywords %}<div>{% for k in e._inserted_keywords %}<span class="kw">{{ k }}</span>{% endfor %}</div>{% endif %}
    </div>
  {% endfor %}{% endif %}

  {% if projects %}<h2>项目经历</h2>
  {% for p in projects %}
    <div class="card em-{{ p._emphasized or 'none' }}">
      <div class="title">{{ p.project_name }} {% if p.role %}· {{ p.role }}{% endif %}</div>
      <div class="meta">{{ p.period }}</div>
      <ul>
        {% if p.star.situation %}<li><b>背景：</b>{{ p.star.situation }}</li>{% endif %}
        {% if p.star.task %}<li><b>目标：</b>{{ p.star.task }}</li>{% endif %}
        {% if p.star.action %}<li><b>行动：</b>{{ p.star.action }}</li>{% endif %}
        {% if p.star.result %}<li><b>结果：</b>{{ p.star.result }}</li>{% endif %}
      </ul>
      {% if p.tech_stack %}<div class="meta">技术：{{ p.tech_stack | join(", ") }}</div>{% endif %}
      {% if p._inserted_keywords %}<div>{% for k in p._inserted_keywords %}<span class="kw">{{ k }}</span>{% endfor %}</div>{% endif %}
    </div>
  {% endfor %}{% endif %}

  {% if abilities %}<h2>核心能力</h2>
  <div>
    {% for a in abilities %}
      <span class="kw">{{ a.skill_name }}{% if a.level %} · Lv{{ a.level }}{% endif %}</span>
    {% endfor %}
  </div>{% endif %}
</body></html>
```

- [ ] **Step 4：en 模板**

`apps/api/src/templates/resume/en_simple.html`：与 zh 同结构，仅文案/标题英文化：
```html
<!doctype html><html lang="en"><head><meta charset="utf-8"><style>{{ css }}</style></head><body>
<h1>{{ basic.name or "" }}</h1>
<div class="basic">
  {% if basic.phone %}{{ basic.phone }} · {% endif %}
  {% if basic.email %}{{ basic.email }} · {% endif %}{{ basic.location or "" }}
</div>
{% if experiences %}<h2>Experience</h2>
{% for e in experiences %}<div class="card em-{{ e._emphasized or 'none' }}">
  <div class="title">{{ e.company_display }} — {{ e.title }}</div>
  <div class="meta">{{ e.period }} · {{ e.industry or "" }}</div>
  {% if e.scope %}<div>{{ e.scope }}</div>{% endif %}
  {% if e.achievements %}<ul>{% for a in e.achievements %}<li>{{ a }}</li>{% endfor %}</ul>{% endif %}
</div>{% endfor %}{% endif %}
{% if projects %}<h2>Projects</h2>
{% for p in projects %}<div class="card em-{{ p._emphasized or 'none' }}">
  <div class="title">{{ p.project_name }}{% if p.role %} · {{ p.role }}{% endif %}</div>
  <div class="meta">{{ p.period }}</div>
  <ul>
    {% if p.star.situation %}<li><b>Context:</b> {{ p.star.situation }}</li>{% endif %}
    {% if p.star.task %}<li><b>Goal:</b> {{ p.star.task }}</li>{% endif %}
    {% if p.star.action %}<li><b>Action:</b> {{ p.star.action }}</li>{% endif %}
    {% if p.star.result %}<li><b>Result:</b> {{ p.star.result }}</li>{% endif %}
  </ul>
</div>{% endfor %}{% endif %}
{% if abilities %}<h2>Skills</h2>
<div>{% for a in abilities %}<span class="kw">{{ a.skill_name }}</span>{% endfor %}</div>{% endif %}
</body></html>
```

- [ ] **Step 5：template_renderer.py**

```python
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

TPL_DIR = Path(__file__).parent.parent / "templates" / "resume"
_env = Environment(loader=FileSystemLoader(str(TPL_DIR)), autoescape=select_autoescape(["html"]))
_CSS = (TPL_DIR / "base.css").read_text(encoding="utf-8")

MASK_LABELS = {
    "zh": "某知名互联网公司",
    "en": "Major Tech Company",
}

def _filter(cards: list[dict]) -> list[dict]:
    return [c for c in cards if not c.get("_hidden")]

def render_html(rendered: dict, language: str, mask_current_company: bool) -> str:
    tpl = _env.get_template("zh_simple.html" if language == "zh" else "en_simple.html")
    basic = rendered.get("basic_info", {})
    experiences = _filter(rendered.get("experience_cards", []))
    if mask_current_company:
        for e in experiences:
            if e.get("is_current"):
                e["company_display"] = MASK_LABELS.get(language, MASK_LABELS["zh"])
            else:
                e["company_display"] = e.get("company", "")
    else:
        for e in experiences:
            e["company_display"] = e.get("company", "")
    return tpl.render(
        css=_CSS,
        basic=basic,
        experiences=experiences,
        projects=_filter(rendered.get("project_cards", [])),
        abilities=_filter(rendered.get("ability_cards", [])),
    )
```

- [ ] **Step 6：测试**

```python
from src.services.template_renderer import render_html

DATA = {
  "basic_info": {"name":"张三","email":"a@b.com"},
  "experience_cards": [
    {"id":"e1","company":"字节","title":"PM","period":"2020-至今","is_current":True,
     "_emphasized":"high","_hidden":False},
  ],
  "project_cards":[], "ability_cards":[{"id":"a1","skill_name":"增长","level":4}],
}

def test_zh_renders_with_mask():
    html = render_html(DATA, "zh", mask_current_company=True)
    assert "某知名互联网公司" in html
    assert "字节" not in html
    assert "张三" in html

def test_en_renders_without_mask():
    html = render_html(DATA, "en", mask_current_company=False)
    assert "字节" in html
    assert "Experience" in html
```

Run: PASS

- [ ] **Step 7：提交**

```bash
git add apps/api && git commit -m "feat(api): bilingual (zh/en) resume HTML templates with masking and emphasis styles"
```

---

## Task 7: PDF Renderer + Export Endpoint

**Files:**
- Create: `apps/api/src/services/pdf_renderer.py`
- Modify: `apps/api/src/routers/resume_branch.py`（追加 export 路由）
- Create: `apps/api/tests/test_pdf_renderer.py`

**Interfaces:**
- Produces:
  - `render_pdf(html: str) -> bytes`（WeasyPrint）
  - `POST /api/v1/applications/{app_id}/branches/{branch_id}/export` body `{language?, mask_current_company?}` → 渲染 + 上传 S3 → 返回 `{pdf_url}`

- [ ] **Step 1：装 weasyprint**

```bash
cd apps/api && source .venv/bin/activate
pip install weasyprint==62.3
```
注：macOS 需 `brew install pango`；Linux 需 `apt install libpango-1.0-0 libpangoft2-1.0-0`；Windows 需 GTK runtime（Plan 0 README 补一行说明）。
`pyproject.toml` 追加：`"weasyprint==62.3",`

- [ ] **Step 2：pdf_renderer.py**

```python
from weasyprint import HTML

def render_pdf(html: str) -> bytes:
    return HTML(string=html).write_pdf()
```

- [ ] **Step 3：扩 router**

追加到 `resume_branch.py`：
```python
from pydantic import BaseModel
from uuid import uuid4
from src.services.template_renderer import render_html
from src.services.pdf_renderer import render_pdf
from src.services.storage import presign_get, _client

class ExportIn(BaseModel):
    language: str | None = None
    mask_current_company: bool = True

class ExportOut(BaseModel):
    pdf_url: str

@router.post("/{branch_id}/export", response_model=ExportOut)
def export_branch(app_id: UUID, branch_id: UUID, body: ExportIn,
                  user: User = Depends(current_user), db: Session = Depends(get_db)) -> ExportOut:
    _get_app(app_id, user, db)
    b = db.query(ResumeBranch).filter(ResumeBranch.id == branch_id, ResumeBranch.application_id == app_id).first()
    if not b: raise HTTPException(404, "branch not found")
    r = _get_master(user, db)
    master = _serialize_master(r)
    rendered = apply_operations(master, b.patch)
    rendered["basic_info"] = r.basic_info or {}
    lang = body.language or b.language or "zh"
    html = render_html(rendered, lang, body.mask_current_company)
    pdf_bytes = render_pdf(html)
    key = f"users/{user.id}/exports/{branch_id}-{uuid4()}.pdf"
    from src.core.config import get_settings
    _client().put_object(Bucket=get_settings().s3_bucket, Key=key, Body=pdf_bytes, ContentType="application/pdf")
    url = presign_get(key, expires_in=7*86400)
    b.exported_pdf_urls = [*(b.exported_pdf_urls or []), {"key": key, "url": url, "language": lang, "masked": body.mask_current_company}]
    db.commit()
    return ExportOut(pdf_url=url)
```

- [ ] **Step 4：测试（mock weasyprint + storage）**

```python
from unittest.mock import patch, MagicMock
# 简单单元：render_pdf 与 export endpoint
def test_render_pdf_returns_bytes():
    from src.services.pdf_renderer import render_pdf
    with patch("src.services.pdf_renderer.HTML") as MH:
        MH.return_value.write_pdf.return_value = b"%PDF-..."
        out = render_pdf("<html></html>")
    assert out.startswith(b"%PDF")
```

Run: PASS

- [ ] **Step 5：提交**

```bash
cd ../.. && git add apps/api && git commit -m "feat(api): PDF export endpoint (WeasyPrint -> S3) with masking and language selection"
```

---

## Task 8: Web — ResumeBranch Hooks

**Files:**
- Create: `apps/web/src/hooks/useResumeBranches.ts`

**Interfaces:**
- Produces:
  - `useBranches(appId)` / `useBranch(appId, branchId)` / `useGenerateBranch(appId)` / `useUpdateBranch(appId, branchId)` / `useRollback(appId)` / `useExportBranch(appId, branchId)` / `useDeleteBranch(appId, branchId)`

- [ ] **Step 1：写 hooks**

```typescript
'use client'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'

const key = (appId: string, branchId?: string) => branchId ? ['branches', appId, branchId] : ['branches', appId]

export function useBranches(appId: string) {
  return useQuery({ queryKey: key(appId), queryFn: () => api<any[]>(`/api/v1/applications/${appId}/branches`), enabled: !!appId })
}

export function useBranch(appId: string, branchId: string) {
  return useQuery({ queryKey: key(appId, branchId), queryFn: () => api<any>(`/api/v1/applications/${appId}/branches/${branchId}`), enabled: !!branchId })
}

export function useGenerateBranch(appId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { language?: string }) => api<any>(`/api/v1/applications/${appId}/branches`, { method: 'POST', body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['branches', appId] }),
  })
}

export function useUpdateBranch(appId: string, branchId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { patch: any[] }) => api<any>(`/api/v1/applications/${appId}/branches/${branchId}`, { method: 'PATCH', body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['branches', appId] }),
  })
}

export function useRollback(appId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (vars: { branchId: string; prevId: string }) =>
      api<any>(`/api/v1/applications/${appId}/branches/${vars.branchId}/rollback-to/${vars.prevId}`, { method: 'POST' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['branches', appId] }),
  })
}

export function useDeleteBranch(appId: string, branchId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => api(`/api/v1/applications/${appId}/branches/${branchId}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['branches', appId] }),
  })
}

export function useExportBranch(appId: string, branchId: string) {
  return useMutation({
    mutationFn: (body: { language?: string; mask_current_company?: boolean }) =>
      api<{ pdf_url: string }>(`/api/v1/applications/${appId}/branches/${branchId}/export`, { method: 'POST', body: JSON.stringify(body) }),
  })
}
```

- [ ] **Step 2：提交**

```bash
git add apps/web && git commit -m "feat(web): resume branch hooks (CRUD + generate + rollback + export)"
```

---

## Task 9: Web — 简历定制主页布局

**Files:**
- Modify: `apps/web/src/app/[locale]/(app)/opportunities/[id]/resume/page.tsx`
- Create: `apps/web/src/components/resume/JDInsightPanel.tsx`
- Create: `apps/web/src/components/resume/BranchSwitcher.tsx`
- Create: `apps/web/src/components/resume/GenerateButton.tsx`
- Modify: `apps/web/messages/{zh,en}.json`

**Interfaces:**
- Produces:
  - 左栏：JD 解读（关键词/隐性偏好/雷区/评分）
  - 右栏：当前分支双视图（Task 10 实现）+ 顶部 BranchSwitcher
  - 无任何分支时显示 "生成第一版定制简历" 大按钮

- [ ] **Step 1：翻译**

zh.json 追加：
```json
"resume_tab": {
  "title":"简历定制",
  "no_branch":"暂无定制版本",
  "generate_first":"生成第一版定制简历",
  "generate_next":"再生成一版",
  "language":"语言","mask":"现公司脱敏",
  "match_score":"匹配评分",
  "keywords":"关键词","preferences":"隐性偏好","red_flags":"雷区",
  "export_pdf":"导出 PDF","coach":"找 Coach 锐评"
}
```

en.json 对应英文。

- [ ] **Step 2：JDInsightPanel**

```typescript
'use client'
import { useTranslations } from 'next-intl'

export function JDInsightPanel({ jp, matchScore }: { jp: any; matchScore: number | null }) {
  const t = useTranslations('resume_tab')
  const reqs = jp?.requirements_parsed ?? {}
  return (
    <aside className="w-72 border-r pr-4 space-y-3 text-sm">
      <div>
        <div className="text-xs text-gray-500">{t('match_score')}</div>
        <div className="text-3xl font-bold">{matchScore ?? '—'} <span className="text-base">/ 100</span></div>
      </div>
      <Block title={t('keywords')} items={[...(reqs.hard ?? []), ...(reqs.soft ?? [])]} />
      <Block title={t('preferences')} items={jp?.hidden_preferences ?? []} />
      <Block title={t('red_flags')} items={jp?.red_flags ?? []} />
    </aside>
  )
}

function Block({ title, items }: { title: string; items: string[] }) {
  if (!items?.length) return null
  return (
    <div>
      <div className="font-semibold mb-1">{title}</div>
      <ul className="list-disc pl-5">{items.map((x, i) => <li key={i}>{x}</li>)}</ul>
    </div>
  )
}
```

- [ ] **Step 3：BranchSwitcher**

```typescript
'use client'
import { useBranches, useDeleteBranch } from '@/hooks/useResumeBranches'

export function BranchSwitcher({ appId, currentId, onPick }: { appId: string; currentId: string | null; onPick: (id: string) => void }) {
  const { data } = useBranches(appId)
  return (
    <div className="flex items-center gap-2 flex-wrap">
      {(data ?? []).map((b: any) => (
        <button key={b.id} onClick={() => onPick(b.id)}
                className={`px-3 py-1 border rounded ${b.id === currentId ? 'bg-black text-white' : ''}`}>
          {b.version_label} {b.match_score != null && `· ${b.match_score}`}
        </button>
      ))}
    </div>
  )
}
```

- [ ] **Step 4：GenerateButton**

```typescript
'use client'
import { useTranslations } from 'next-intl'
import { useGenerateBranch } from '@/hooks/useResumeBranches'

export function GenerateButton({ appId, isFirst, onGenerated }: { appId: string; isFirst: boolean; onGenerated: (id: string) => void }) {
  const t = useTranslations('resume_tab')
  const gen = useGenerateBranch(appId)
  async function go() {
    const b = await gen.mutateAsync({})
    onGenerated(b.id)
  }
  return (
    <button onClick={go} disabled={gen.isPending}
            className={`${isFirst ? 'w-full py-6 text-lg' : 'px-4 py-2'} bg-blue-600 text-white rounded disabled:opacity-50`}>
      {gen.isPending ? '生成中…' : (isFirst ? t('generate_first') : t('generate_next'))}
    </button>
  )
}
```

- [ ] **Step 5：resume/page.tsx 主布局**

```typescript
'use client'
import { use, useEffect, useState } from 'react'
import { useTranslations } from 'next-intl'
import { useApplication } from '@/hooks/useApplications'
import { useBranches, useBranch } from '@/hooks/useResumeBranches'
import { JDInsightPanel } from '@/components/resume/JDInsightPanel'
import { BranchSwitcher } from '@/components/resume/BranchSwitcher'
import { GenerateButton } from '@/components/resume/GenerateButton'
import { ResumeWorkspace } from '@/components/resume/ResumeWorkspace' // Task 10

export default function ResumeTab({ params }: { params: Promise<{ id: string }> }) {
  const { id: appId } = use(params)
  const t = useTranslations('resume_tab')
  const { data: appData } = useApplication(appId)
  const { data: branches } = useBranches(appId)
  const [activeId, setActiveId] = useState<string | null>(null)

  useEffect(() => {
    if (branches?.length && !activeId) {
      const active = branches.find((b: any) => b.is_active) ?? branches[0]
      setActiveId(active.id)
    }
  }, [branches, activeId])

  const { data: branch } = useBranch(appId, activeId ?? '')

  return (
    <div className="flex gap-6 min-h-[60vh]">
      <JDInsightPanel jp={appData?.job_posting} matchScore={branch?.match_score ?? null} />
      <section className="flex-1 space-y-4">
        <div className="flex items-center justify-between">
          <BranchSwitcher appId={appId} currentId={activeId} onPick={setActiveId} />
          <GenerateButton appId={appId} isFirst={!branches?.length} onGenerated={setActiveId} />
        </div>
        {!branches?.length && <p className="text-gray-500">{t('no_branch')}</p>}
        {branch && <ResumeWorkspace appId={appId} branch={branch} />}
      </section>
    </div>
  )
}
```

- [ ] **Step 6：提交**

```bash
git add apps/web && git commit -m "feat(web): resume customization page layout (jd panel + branch switcher + generate)"
```

---

## Task 10: Web — 双视图 / 单视图 / 合并预览（三模式）

**Files:**
- Create: `apps/web/src/components/resume/ResumeWorkspace.tsx`
- Create: `apps/web/src/components/resume/RenderedResume.tsx`
- Create: `apps/web/src/components/resume/DiffView.tsx`

**Interfaces:**
- Produces:
  - `<ResumeWorkspace>` 包含模式切换（diff / sidebyside / merge）
  - `<RenderedResume>` 接受 rendered_resume 渲染卡片视图
  - `<DiffView>` 高亮被改/被强调/被隐藏的卡片
  - merge 模式 = 单视图（仅 rendered），sidebyside = 并排（master + rendered），diff = 单视图但带高亮

- [ ] **Step 1：RenderedResume**

```typescript
'use client'
export function RenderedResume({ data, highlight = false }: { data: any; highlight?: boolean }) {
  return (
    <div className="space-y-4">
      <Section title="工作经历">
        {(data.experience_cards ?? []).map((e: any) => (
          <Card key={e.id} emphasis={highlight ? e._emphasized : 'none'} hidden={highlight && e._hidden}>
            <div className="font-bold">{e.company} — {e.title}</div>
            <div className="text-xs text-gray-500">{e.period} · {e.industry}</div>
            <div className="text-sm">{e.scope}</div>
            {(e.achievements ?? []).map((a: string, i: number) => <div key={i} className="text-sm">• {a}</div>)}
          </Card>
        ))}
      </Section>
      <Section title="项目经历">
        {(data.project_cards ?? []).map((p: any) => (
          <Card key={p.id} emphasis={highlight ? p._emphasized : 'none'} hidden={highlight && p._hidden}
                patched={highlight && (p._patched_fields?.length > 0)}>
            <div className="font-bold">{p.project_name} {p.role && `· ${p.role}`}</div>
            <div className="text-xs text-gray-500">{p.period}</div>
            <ul className="text-sm pl-4 list-disc">
              {p.star?.situation && <li><b>背景：</b>{p.star.situation}</li>}
              {p.star?.task && <li><b>目标：</b>{p.star.task}</li>}
              {p.star?.action && <li><b>行动：</b>{p.star.action}</li>}
              {p.star?.result && <li><b>结果：</b>{p.star.result}</li>}
            </ul>
            {highlight && p._inserted_keywords?.length > 0 && (
              <div className="mt-1">{p._inserted_keywords.map((k: string, i: number) => <span key={i} className="text-xs bg-blue-100 text-blue-700 rounded px-2 py-0.5 mr-1">+{k}</span>)}</div>
            )}
          </Card>
        ))}
      </Section>
      <Section title="核心能力">
        <div className="flex flex-wrap gap-2">
          {(data.ability_cards ?? []).map((a: any) => (
            <span key={a.id} className={`text-xs border rounded px-2 py-1 ${highlight && a._emphasized === 'high' ? 'bg-yellow-100 border-yellow-400' : ''} ${highlight && a._hidden ? 'opacity-30 line-through' : ''}`}>
              {a.skill_name} Lv{a.level}
            </span>
          ))}
        </div>
      </Section>
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return <div><h3 className="font-bold border-b pb-1 mb-2">{title}</h3>{children}</div>
}

function Card({ children, emphasis, hidden, patched }: { children: React.ReactNode; emphasis?: string; hidden?: boolean; patched?: boolean }) {
  if (hidden) return <div className="border rounded p-2 opacity-30 line-through">{children}</div>
  const bg = emphasis === 'high' ? 'bg-yellow-50 border-yellow-400'
           : emphasis === 'medium' ? 'bg-yellow-50/50'
           : patched ? 'bg-blue-50 border-blue-300' : ''
  return <div className={`border rounded p-3 ${bg}`}>{children}</div>
}
```

- [ ] **Step 2：DiffView (本质上是 RenderedResume highlight=true)**

```typescript
'use client'
import { RenderedResume } from './RenderedResume'
export function DiffView({ rendered }: { rendered: any }) {
  return <RenderedResume data={rendered} highlight />
}
```

- [ ] **Step 3：ResumeWorkspace**

```typescript
'use client'
import { useState } from 'react'
import { RenderedResume } from './RenderedResume'
import { DiffView } from './DiffView'
import { PatchReasoning } from './PatchReasoning'  // Task 11
import { ExportDialog } from './ExportDialog'      // Task 12
import { CoachInquiryButton } from '@/components/coach/CoachInquiryButton'  // Task 13

type Mode = 'diff' | 'side' | 'merge'

export function ResumeWorkspace({ appId, branch }: { appId: string; branch: any }) {
  const [mode, setMode] = useState<Mode>('side')
  const [exportOpen, setExportOpen] = useState(false)
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        {(['diff','side','merge'] as Mode[]).map((m) => (
          <button key={m} onClick={() => setMode(m)} className={`px-3 py-1 text-sm border rounded ${mode === m ? 'bg-black text-white' : ''}`}>
            {m === 'diff' ? 'Diff 高亮' : m === 'side' ? '并排对比' : '合并预览'}
          </button>
        ))}
        <div className="ml-auto flex gap-2">
          <button onClick={() => setExportOpen(true)} className="px-3 py-1 text-sm bg-blue-600 text-white rounded">📤 导出 PDF</button>
          <CoachInquiryButton appId={appId} branchId={branch.id} />
        </div>
      </div>

      {mode === 'side' ? (
        <div className="grid grid-cols-2 gap-4">
          <Panel title="主版本"><RenderedResume data={branch.master_snapshot} /></Panel>
          <Panel title={`补丁 ${branch.version_label}`}><DiffView rendered={branch.rendered_resume} /></Panel>
        </div>
      ) : mode === 'diff' ? (
        <Panel title={`补丁 ${branch.version_label} · Diff 高亮`}><DiffView rendered={branch.rendered_resume} /></Panel>
      ) : (
        <Panel title="合并预览（导出前所见即所得）"><RenderedResume data={branch.rendered_resume} /></Panel>
      )}

      <PatchReasoning reasoning={branch.ai_reasoning} />

      {exportOpen && <ExportDialog appId={appId} branchId={branch.id} defaultLang={branch.language} onClose={() => setExportOpen(false)} />}
    </div>
  )
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return <div className="border rounded p-3"><h4 className="font-bold mb-2 text-sm">{title}</h4>{children}</div>
}
```

- [ ] **Step 4：提交**

```bash
git add apps/web && git commit -m "feat(web): ResumeWorkspace with diff/sidebyside/merge modes + RenderedResume + DiffView"
```

---

## Task 11: Web — PatchReasoning（AI 修改理由透明化）

**Files:**
- Create: `apps/web/src/components/resume/PatchReasoning.tsx`

**Interfaces:**
- Produces:
  - 折叠列表：每条 `{op_index, reason}` 显示一条；点击可定位到对应卡片（v1 简化为高亮一下）

- [ ] **Step 1**

```typescript
'use client'
import { useState } from 'react'

export function PatchReasoning({ reasoning }: { reasoning: { op_index: number; reason: string }[] }) {
  const [open, setOpen] = useState(true)
  if (!reasoning?.length) return null
  return (
    <details open={open} onToggle={(e) => setOpen((e.target as HTMLDetailsElement).open)} className="border rounded p-3">
      <summary className="cursor-pointer font-semibold text-sm">AI 修改理由（{reasoning.length}）</summary>
      <ol className="mt-2 space-y-1 text-sm pl-5 list-decimal">
        {reasoning.map((r, i) => <li key={i}>{r.reason}</li>)}
      </ol>
    </details>
  )
}
```

- [ ] **Step 2：提交**

```bash
git add apps/web && git commit -m "feat(web): PatchReasoning collapsible panel for AI edits transparency"
```

---

## Task 12: Web — ExportDialog（语言 + 脱敏开关）

**Files:**
- Create: `apps/web/src/components/resume/ExportDialog.tsx`

**Interfaces:**
- Produces:
  - 选 zh/en
  - 切换"现公司脱敏"（默认 ON，附说明）
  - 点击导出 → 下载 PDF

- [ ] **Step 1**

```typescript
'use client'
import { useState } from 'react'
import { useExportBranch } from '@/hooks/useResumeBranches'

export function ExportDialog({ appId, branchId, defaultLang, onClose }: { appId: string; branchId: string; defaultLang: string; onClose: () => void }) {
  const exp = useExportBranch(appId, branchId)
  const [lang, setLang] = useState(defaultLang)
  const [mask, setMask] = useState(true)
  const [url, setUrl] = useState<string | null>(null)

  async function go() {
    const r = await exp.mutateAsync({ language: lang, mask_current_company: mask })
    setUrl(r.pdf_url)
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center" onClick={onClose}>
      <div className="bg-white rounded p-6 w-96" onClick={(e) => e.stopPropagation()}>
        <h3 className="font-bold">导出 PDF</h3>
        <div className="space-y-3 mt-3 text-sm">
          <div>
            <label className="block mb-1">语言</label>
            <select value={lang} onChange={(e) => setLang(e.target.value)} className="w-full border rounded px-2 py-1">
              <option value="zh">中文</option>
              <option value="en">English</option>
            </select>
          </div>
          <label className="flex items-start gap-2">
            <input type="checkbox" checked={mask} onChange={(e) => setMask(e.target.checked)} className="mt-1" />
            <span>
              <b>现公司脱敏</b><br />
              <span className="text-xs text-gray-500">勾选后，现公司名导出为「某知名互联网公司」，避免投递时暴露</span>
            </span>
          </label>
          {url && (
            <a href={url} target="_blank" rel="noreferrer" className="block text-center bg-green-600 text-white py-2 rounded">⬇ 下载 PDF</a>
          )}
        </div>
        <div className="flex justify-end gap-2 mt-4">
          <button onClick={onClose} className="px-3 py-2">关闭</button>
          <button onClick={go} disabled={exp.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50">
            {exp.isPending ? '导出中…' : (url ? '重新导出' : '导出')}
          </button>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2：提交**

```bash
git add apps/web && git commit -m "feat(web): export dialog with language + mask_current_company toggle"
```

---

## Task 13: Web — Coach 导流入口（占位组件，详细在 Plan 7）

**Files:**
- Create: `apps/web/src/components/coach/CoachInquiryButton.tsx`
- Create: `apps/web/src/components/coach/CoachInquiryDrawer.tsx`

**Interfaces:**
- Produces:
  - `<CoachInquiryButton appId, branchId, source="resume_workspace">` → 点击打开抽屉
  - 抽屉里：简短说明 + 微信号联系（v1 直接放二维码图 + 暂存联系方式到本地，正式表单接 Plan 7 endpoint）

- [ ] **Step 1：Button + Drawer 占位**

```typescript
'use client'
import { useState } from 'react'
import { CoachInquiryDrawer } from './CoachInquiryDrawer'

export function CoachInquiryButton({ appId, branchId }: { appId: string; branchId?: string }) {
  const [open, setOpen] = useState(false)
  return (
    <>
      <button onClick={() => setOpen(true)} className="px-3 py-1 text-sm border border-blue-600 text-blue-600 rounded">
        💬 找 Coach 锐评
      </button>
      {open && <CoachInquiryDrawer appId={appId} branchId={branchId} onClose={() => setOpen(false)} />}
    </>
  )
}
```

```typescript
'use client'
export function CoachInquiryDrawer({ appId, branchId, onClose }: { appId: string; branchId?: string; onClose: () => void }) {
  // v1 极简：展示说明 + 微信号；Plan 7 接 /api/v1/coach/inquiries 表单
  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center" onClick={onClose}>
      <div className="bg-white rounded p-6 w-96" onClick={(e) => e.stopPropagation()}>
        <h3 className="font-bold">找 Coach 锐评（500-2000）</h3>
        <p className="text-sm mt-2">
          1 对 1 真人 coach 给你这份简历做"招聘方视角"深度锐评，约 30-60 分钟。
        </p>
        <p className="text-xs text-gray-500 mt-1">本周 5 个名额，先到先得。</p>
        <div className="mt-4 text-sm">
          联系微信：<b>jc-coach-001</b>（v1 表单待 Plan 7 上线）
        </div>
        <button onClick={onClose} className="mt-4 w-full bg-black text-white py-2 rounded">复制并关闭</button>
      </div>
    </div>
  )
}
```

- [ ] **Step 2：提交**

```bash
git add apps/web && git commit -m "feat(web): coach inquiry button + drawer (placeholder, full form in Plan 7)"
```

---

## Task 14: PostHog Events + e2e Smoke

**Files:**
- Modify: `packages/shared-types/events.ts`
- Modify: `apps/web/src/hooks/useResumeBranches.ts`（onSuccess track）
- Create: `apps/web/e2e/resume.spec.ts`

**Interfaces:**
- Produces:
  - 事件：`RESUME_BRANCH_GENERATED`、`RESUME_BRANCH_EXPORTED`、`RESUME_BRANCH_ROLLBACK`、`RESUME_MODE_SWITCHED`、`COACH_INQUIRY_OPENED`

- [ ] **Step 1：events**

```typescript
export const Events = {
  // ...
  RESUME_BRANCH_GENERATED: 'resume_branch_generated',
  RESUME_BRANCH_EXPORTED: 'resume_branch_exported',
  RESUME_BRANCH_ROLLBACK: 'resume_branch_rollback',
  RESUME_MODE_SWITCHED: 'resume_mode_switched',
  COACH_INQUIRY_OPENED: 'coach_inquiry_opened',
} as const
```

- [ ] **Step 2：track 在 generate / export / rollback / mode-switch / coach-open**

例：
```typescript
// useGenerateBranch
onSuccess: (b: any) => { track(Events.RESUME_BRANCH_GENERATED, { match_score: b.match_score, lang: b.language }); ... }

// useExportBranch
onSuccess: (r: any, vars) => { track(Events.RESUME_BRANCH_EXPORTED, { lang: vars.language, masked: vars.mask_current_company }) }

// ResumeWorkspace mode change: track(Events.RESUME_MODE_SWITCHED, { mode })
// CoachInquiryButton onClick: track(Events.COACH_INQUIRY_OPENED, { appId, branchId, source: 'resume_workspace' })
```

- [ ] **Step 3：e2e**

```typescript
import { test, expect } from '@playwright/test'

test('resume tab UI smoke (unauth state still renders shell)', async ({ page }) => {
  await page.goto('/zh/opportunities')
  await expect(page.getByRole('heading', { name: '我的求职机会' })).toBeVisible()
})
```

完整登录态 e2e 在用户接入 PostHog/auth 后补。

- [ ] **Step 4：提交**

```bash
git add packages apps && git commit -m "feat: posthog events for resume customization + e2e smoke"
```

---

## Plan 3 完成判定

```bash
pnpm --filter api test && pnpm --filter web typecheck && pnpm --filter web e2e
# 手动 e2e
# 1) 上传主简历 (Plan 1) → 创建机会 (Plan 2) → 进入简历定制 Tab
# 2) 点"生成第一版" → 看到双视图 + diff 高亮 + AI 修改理由列表 + 评分
# 3) 切换三模式 → 切换分支版本 → 一键导出 PDF → 浏览器下载到本地中文/英文 PDF
# 4) 切现公司脱敏 → 重新导出 → company 已变为"某知名互联网公司"
```

下一站 → Plan 4 (ResourceItem + Collection)
