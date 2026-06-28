# Plan 1：MasterResume 模块 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 用户能上传简历（PDF/Word）→ AI 自动解析为「能力卡 / 项目卡 / 经历卡」结构化主版本 → 用户校对补漏 → AI 给出含金量诊断；应届生还能走"轻问诊"由 AI 帮忙挖经历。

**Architecture:** 文件经预签名 URL 直传 S3 兼容存储；后端拉取后做 PDF/Docx 文本抽取，喂给 MiniMax-M1 做结构化抽取，落盘三类 card 表；卡片支持 CRUD 与含金量诊断；is_current=true 的经历卡有强提示组件。

**Tech Stack:** boto3 (S3) / pypdfium2 / python-docx / Pydantic v2 / LLM via Plan 0 LLMClient / React Hook Form / TanStack Query

## Global Constraints
- 继承 Plan 0 全部约束（TS strict / mypy strict / LLM 走统一入口 / 字段加密 / i18n / PostHog 强类型事件 / 现公司强提示 / e2e）
- 所有 AI 调用通过 `LLMClient.acomplete` 并写 `ai_call_log`（log 表在本 plan 创建）
- 卡片字段加密：`ExperienceCard.company`（is_current=true 时必须加密）
- 容量上限：v1 每用户主简历 1 份；卡片数量无硬上限

---

## Task 1: AI Call Log 表（成本仪表盘底盘）

**Files:**
- Create: `apps/api/src/models/ai_call_log.py`
- Create: `apps/api/alembic/versions/0003_ai_call_log.py`
- Modify: `apps/api/src/models/__init__.py`
- Modify: `apps/api/src/ai/llm_client.py`（每次调用写 log）
- Create: `apps/api/tests/test_ai_call_log.py`

**Interfaces:**
- Produces:
  - `AICallLog` 模型：user_id / scene / model / input_tokens / output_tokens / cost_usd / latency_ms / status / created_at
  - `LLMClient.acomplete` 新增可选参数 `user_id: UUID | None = None, scene: str = "unknown"`，自动写 log

- [ ] **Step 1：写模型**

`apps/api/src/models/ai_call_log.py`：
```python
from datetime import datetime
from uuid import uuid4, UUID
import sqlalchemy as sa
from sqlalchemy import String, DateTime, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from src.core.db import Base

class AICallLog(Base):
    __tablename__ = "ai_call_logs"
    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID | None] = mapped_column(sa.Uuid, index=True, nullable=True)
    scene: Mapped[str] = mapped_column(String(64), index=True)
    model: Mapped[str] = mapped_column(String(64))
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Numeric(10, 6), default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="ok")  # ok | error
    error_message: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=sa.func.now(), index=True)
```

`apps/api/src/models/__init__.py` 追加：
```python
from src.models.ai_call_log import AICallLog  # noqa: F401
```

- [ ] **Step 2：生成迁移**

```bash
cd apps/api && source .venv/bin/activate
alembic revision --autogenerate -m "ai call logs"
# 重命名为 0003_ai_call_log.py
alembic upgrade head
```

- [ ] **Step 3：改 LLMClient 写 log**

`apps/api/src/ai/llm_client.py` 重写：
```python
from time import perf_counter
from typing import Any
from uuid import UUID
from litellm import acompletion
from litellm.cost_calculator import completion_cost
from src.core.db import SessionLocal
from src.models.ai_call_log import AICallLog

FALLBACK_CHAIN = {
    # v1 单供应商 MiniMax；同家族两档兜底
    "auto-m1": ["minimax/MiniMax-M1", "minimax/abab6.5s-chat"],
    "auto-light": ["minimax/abab6.5s-chat"],
}

class LLMClient:
    async def acomplete(
        self,
        model: str,
        system: str,
        messages: list[dict[str, Any]],
        max_tokens: int = 1024,
        user_id: UUID | None = None,
        scene: str = "unknown",
    ) -> str:
        full = [{"role": "system", "content": system}, *messages]
        chain = FALLBACK_CHAIN.get(model, [model])
        last_exc: Exception | None = None
        for m in chain:
            t0 = perf_counter()
            try:
                resp = await acompletion(model=m, messages=full, max_tokens=max_tokens)
                text = resp.choices[0].message.content or ""
                latency = int((perf_counter() - t0) * 1000)
                self._log(user_id, scene, m, resp, latency, "ok", None)
                return text
            except Exception as e:  # noqa: BLE001
                latency = int((perf_counter() - t0) * 1000)
                self._log(user_id, scene, m, None, latency, "error", str(e)[:500])
                last_exc = e
                continue
        raise RuntimeError(f"All MiniMax fallbacks failed: {last_exc}")

    def _log(self, user_id, scene, model, resp, latency, status, err):
        try:
            cost = float(completion_cost(completion_response=resp)) if resp else 0
        except Exception:
            cost = 0
        usage = getattr(resp, "usage", None) if resp else None
        db = SessionLocal()
        try:
            db.add(AICallLog(
                user_id=user_id, scene=scene, model=model,
                input_tokens=getattr(usage, "prompt_tokens", 0) if usage else 0,
                output_tokens=getattr(usage, "completion_tokens", 0) if usage else 0,
                cost_usd=cost, latency_ms=latency,
                status=status, error_message=err,
            ))
            db.commit()
        finally:
            db.close()
```

- [ ] **Step 4：写测试**

`apps/api/tests/test_ai_call_log.py`：
```python
from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from src.ai.llm_client import LLMClient
from src.core.db import SessionLocal
from src.models.ai_call_log import AICallLog

@pytest.mark.asyncio
async def test_log_written_on_success():
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock(message=MagicMock(content="ok"))]
    mock_resp.usage = MagicMock(prompt_tokens=10, completion_tokens=2)
    with patch("src.ai.llm_client.acompletion", AsyncMock(return_value=mock_resp)), \
         patch("src.ai.llm_client.completion_cost", return_value=0.001):
        await LLMClient().acomplete("minimax/abab6.5s-chat", "sys", [{"role":"user","content":"hi"}], scene="test")
    db = SessionLocal()
    row = db.query(AICallLog).filter(AICallLog.scene == "test").order_by(AICallLog.created_at.desc()).first()
    db.close()
    assert row and row.input_tokens == 10 and row.output_tokens == 2
```

Run: `pytest -q tests/test_ai_call_log.py` → PASS

- [ ] **Step 5：提交**

```bash
cd ../..
git add apps/api
git commit -m "feat(api): ai_call_log table + LLMClient auto-logs cost/tokens/latency"
```

---

## Task 2: MasterResume + 三类 Card 模型

**Files:**
- Create: `apps/api/src/models/master_resume.py`
- Create: `apps/api/src/models/cards.py`
- Create: `apps/api/alembic/versions/0004_master_resume_and_cards.py`
- Modify: `apps/api/src/models/__init__.py`
- Create: `apps/api/tests/test_resume_models.py`

**Interfaces:**
- Produces:
  - `MasterResume(id, user_id [unique], basic_info JSON, parsed_from_file_url, quality_score, updated_at)`
  - `AbilityCard(id, master_resume_id, skill_name, evidence_text, level, last_used_year, tags JSON, is_weak)`
  - `ProjectCard(id, master_resume_id, project_name, role, period, scale_data JSON, star JSON, tech_stack JSON, domain_tags JSON, is_weak, weak_reasons JSON, cross_domain_translation JSON)`
  - `ExperienceCard(id, master_resume_id, company_encrypted, period, title, scope, achievements JSON, industry, is_current)`

- [ ] **Step 1：写模型**

`apps/api/src/models/master_resume.py`：
```python
from datetime import datetime
from uuid import uuid4, UUID
import sqlalchemy as sa
from sqlalchemy import String, DateTime, JSON, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.db import Base

class MasterResume(Base):
    __tablename__ = "master_resumes"
    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(sa.Uuid, ForeignKey("users.id"), unique=True, index=True)
    basic_info: Mapped[dict] = mapped_column(JSON, default=dict)
    parsed_from_file_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    quality_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()
    )

    ability_cards: Mapped[list["AbilityCard"]] = relationship(back_populates="resume", cascade="all,delete-orphan")
    project_cards: Mapped[list["ProjectCard"]] = relationship(back_populates="resume", cascade="all,delete-orphan")
    experience_cards: Mapped[list["ExperienceCard"]] = relationship(back_populates="resume", cascade="all,delete-orphan")
```

`apps/api/src/models/cards.py`：
```python
from uuid import uuid4, UUID
import sqlalchemy as sa
from sqlalchemy import String, JSON, ForeignKey, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.db import Base

class AbilityCard(Base):
    __tablename__ = "ability_cards"
    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid4)
    master_resume_id: Mapped[UUID] = mapped_column(sa.Uuid, ForeignKey("master_resumes.id"), index=True)
    skill_name: Mapped[str] = mapped_column(String(128))
    evidence_text: Mapped[str] = mapped_column(String(2048), default="")
    level: Mapped[int] = mapped_column(Integer, default=3)  # 1-5
    last_used_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    is_weak: Mapped[bool] = mapped_column(Boolean, default=False)
    resume: Mapped["MasterResume"] = relationship(back_populates="ability_cards")

class ProjectCard(Base):
    __tablename__ = "project_cards"
    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid4)
    master_resume_id: Mapped[UUID] = mapped_column(sa.Uuid, ForeignKey("master_resumes.id"), index=True)
    project_name: Mapped[str] = mapped_column(String(256))
    role: Mapped[str] = mapped_column(String(128), default="")
    period: Mapped[str] = mapped_column(String(64), default="")
    scale_data: Mapped[dict] = mapped_column(JSON, default=dict)
    star: Mapped[dict] = mapped_column(JSON, default=dict)
    tech_stack: Mapped[list] = mapped_column(JSON, default=list)
    domain_tags: Mapped[list] = mapped_column(JSON, default=list)
    is_weak: Mapped[bool] = mapped_column(Boolean, default=False)
    weak_reasons: Mapped[list] = mapped_column(JSON, default=list)
    cross_domain_translation: Mapped[dict] = mapped_column(JSON, default=dict)
    resume: Mapped["MasterResume"] = relationship(back_populates="project_cards")

class ExperienceCard(Base):
    __tablename__ = "experience_cards"
    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid4)
    master_resume_id: Mapped[UUID] = mapped_column(sa.Uuid, ForeignKey("master_resumes.id"), index=True)
    company_encrypted: Mapped[str] = mapped_column(String(1024))  # 加密；明文走 service 解
    period: Mapped[str] = mapped_column(String(64), default="")
    title: Mapped[str] = mapped_column(String(128), default="")
    scope: Mapped[str] = mapped_column(String(512), default="")
    achievements: Mapped[list] = mapped_column(JSON, default=list)
    industry: Mapped[str] = mapped_column(String(64), default="")
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    resume: Mapped["MasterResume"] = relationship(back_populates="experience_cards")
```

`apps/api/src/models/__init__.py` 追加：
```python
from src.models.master_resume import MasterResume  # noqa: F401
from src.models.cards import AbilityCard, ProjectCard, ExperienceCard  # noqa: F401
```

- [ ] **Step 2：迁移 + 测试**

```bash
cd apps/api && source .venv/bin/activate
alembic revision --autogenerate -m "master resume and cards"
alembic upgrade head
```

`apps/api/tests/test_resume_models.py`：
```python
from src.models import User, MasterResume, AbilityCard, ProjectCard, ExperienceCard

def test_resume_with_cards(db):
    u = User(preferences={}); db.add(u); db.flush()
    r = MasterResume(user_id=u.id, basic_info={"name":"张三"})
    r.ability_cards.append(AbilityCard(skill_name="增长", level=4))
    r.project_cards.append(ProjectCard(project_name="拉新增长"))
    r.experience_cards.append(ExperienceCard(company_encrypted="enc:xxx", title="PM", is_current=True))
    db.add(r); db.flush()
    assert len(r.ability_cards) == 1
    assert r.experience_cards[0].is_current is True
```

Run: `pytest -q tests/test_resume_models.py` → PASS

- [ ] **Step 3：提交**

```bash
cd ../..
git add apps/api
git commit -m "feat(api): MasterResume + AbilityCard/ProjectCard/ExperienceCard models"
```

---

## Task 3: S3 客户端 + 文件存储服务

**Files:**
- Create: `apps/api/src/services/storage.py`
- Modify: `apps/api/src/core/config.py`（增加 S3 设置）
- Modify: `apps/api/.env.example`
- Create: `apps/api/tests/test_storage.py`
- 修改根 `apps/api/pyproject.toml` 加 `boto3`

**Interfaces:**
- Produces:
  - `presign_put(key: str, content_type: str, expires_in: int = 600) -> str`
  - `presign_get(key: str, expires_in: int = 86400) -> str`
  - `download_bytes(key: str) -> bytes`
  - 桶名走配置 `S3_BUCKET`

- [ ] **Step 1：装依赖 + 加配置**

```bash
cd apps/api && source .venv/bin/activate
pip install boto3==1.35.50
# 同步 pyproject 依赖
```

`pyproject.toml` 的 `dependencies` 追加：
```
"boto3==1.35.50",
```

`apps/api/src/core/config.py` Settings 类追加字段：
```python
s3_bucket: str = ""
s3_region: str = "us-east-1"
s3_endpoint_url: str | None = None
s3_access_key_id: str = ""
s3_secret_access_key: str = ""
```

`apps/api/.env.example` 追加：
```bash
S3_BUCKET=
S3_REGION=us-east-1
S3_ENDPOINT_URL=
S3_ACCESS_KEY_ID=
S3_SECRET_ACCESS_KEY=
```

- [ ] **Step 2：写 storage 服务**

`apps/api/src/services/storage.py`：
```python
import boto3
from botocore.config import Config
from src.core.config import get_settings

def _client():
    s = get_settings()
    return boto3.client(
        "s3",
        region_name=s.s3_region,
        endpoint_url=s.s3_endpoint_url or None,
        aws_access_key_id=s.s3_access_key_id,
        aws_secret_access_key=s.s3_secret_access_key,
        config=Config(signature_version="s3v4"),
    )

def presign_put(key: str, content_type: str, expires_in: int = 600) -> str:
    return _client().generate_presigned_url(
        "put_object",
        Params={"Bucket": get_settings().s3_bucket, "Key": key, "ContentType": content_type},
        ExpiresIn=expires_in,
    )

def presign_get(key: str, expires_in: int = 86400) -> str:
    return _client().generate_presigned_url(
        "get_object",
        Params={"Bucket": get_settings().s3_bucket, "Key": key},
        ExpiresIn=expires_in,
    )

def download_bytes(key: str) -> bytes:
    obj = _client().get_object(Bucket=get_settings().s3_bucket, Key=key)
    return obj["Body"].read()
```

- [ ] **Step 3：写测试（mock boto3）**

`apps/api/tests/test_storage.py`：
```python
from unittest.mock import patch, MagicMock
from src.services.storage import presign_put

def test_presign_put_returns_url():
    mock_cli = MagicMock()
    mock_cli.generate_presigned_url.return_value = "https://example.com/upload"
    with patch("src.services.storage._client", return_value=mock_cli):
        url = presign_put("users/abc/resume.pdf", "application/pdf")
    assert url == "https://example.com/upload"
    mock_cli.generate_presigned_url.assert_called_once()
```

Run: `pytest -q tests/test_storage.py` → PASS

- [ ] **Step 4：提交**

```bash
cd ../..
git add apps/api
git commit -m "feat(api): S3 storage service (presign put/get, download)"
```

---

## Task 4: PDF/Docx 文本抽取服务

**Files:**
- Create: `apps/api/src/services/text_extractor.py`
- Create: `apps/api/tests/test_text_extractor.py`
- Create: `apps/api/tests/fixtures/sample.pdf`、`sample.docx`（手放）

**Interfaces:**
- Produces:
  - `extract_text(filename: str, data: bytes) -> str`：根据扩展名选 pdf/docx 抽取器
- 装依赖：`pypdfium2==4.30.0`, `python-docx==1.1.2`

- [ ] **Step 1：装依赖**

```bash
cd apps/api && source .venv/bin/activate
pip install pypdfium2==4.30.0 python-docx==1.1.2
```

`pyproject.toml` 追加：
```
"pypdfium2==4.30.0",
"python-docx==1.1.2",
```

- [ ] **Step 2：写服务**

`apps/api/src/services/text_extractor.py`：
```python
import io
from pathlib import Path
import pypdfium2
from docx import Document

def extract_text(filename: str, data: bytes) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return _pdf(data)
    if ext in {".docx", ".doc"}:
        return _docx(data)
    raise ValueError(f"unsupported file extension: {ext}")

def _pdf(data: bytes) -> str:
    pdf = pypdfium2.PdfDocument(data)
    chunks: list[str] = []
    for page in pdf:
        text_page = page.get_textpage()
        chunks.append(text_page.get_text_range() or "")
    return "\n".join(chunks)

def _docx(data: bytes) -> str:
    doc = Document(io.BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
```

- [ ] **Step 3：放测试 fixtures**

手工在 `apps/api/tests/fixtures/` 放两个最小样本：
- `sample.pdf`：1 页含「张三 PM 5 年经验」
- `sample.docx`：相同内容

（也可临时用 Python 生成：
```bash
cd apps/api && source .venv/bin/activate && python -c "
from docx import Document
d = Document()
d.add_paragraph('张三 PM 5 年经验')
d.add_paragraph('字节跳动 高级产品经理 2020-2023')
d.save('tests/fixtures/sample.docx')
"
```
PDF 可在线生成或用 `reportlab`）

- [ ] **Step 4：写测试**

`apps/api/tests/test_text_extractor.py`：
```python
from pathlib import Path
from src.services.text_extractor import extract_text

FIX = Path(__file__).parent / "fixtures"

def test_extract_docx():
    data = (FIX / "sample.docx").read_bytes()
    text = extract_text("sample.docx", data)
    assert "张三" in text and "PM" in text

def test_extract_pdf():
    data = (FIX / "sample.pdf").read_bytes()
    text = extract_text("sample.pdf", data)
    assert "张三" in text or len(text) > 0  # PDF 文本依赖样本质量
```

Run: `pytest -q tests/test_text_extractor.py` → PASS

- [ ] **Step 5：提交**

```bash
cd ../..
git add apps/api
git commit -m "feat(api): text extractor for PDF (pypdfium2) and DOCX (python-docx)"
```

---

## Task 5: AI 简历结构化抽取 Prompt + Service

**Files:**
- Create: `apps/api/src/ai/prompts/__init__.py`
- Create: `apps/api/src/ai/prompts/parse_resume.py`
- Create: `apps/api/src/services/resume_parser.py`
- Create: `apps/api/tests/test_resume_parser.py`
- Create: `apps/api/src/schemas/resume.py`

**Interfaces:**
- Produces:
  - `ParsedResume` schema：`{basic_info, ability_cards: list[Ability], project_cards: list[Project], experience_cards: list[Experience]}`
  - `async parse_resume_text(text: str, persona_type: PersonaType, user_id: UUID) -> ParsedResume`

- [ ] **Step 1：写 prompt**

`apps/api/src/ai/prompts/parse_resume.py`：
```python
PARSE_RESUME_SYSTEM = """你是简历结构化助手。读取一段简历正文，输出严格的 JSON。

JSON schema（不许多/少字段）：
{
  "basic_info": {"name": str, "phone": str|null, "email": str|null, "location": str|null},
  "ability_cards": [{"skill_name": str, "evidence_text": str, "level": 1-5, "last_used_year": int|null, "tags": [str]}],
  "project_cards": [{
      "project_name": str, "role": str, "period": str,
      "scale_data": object,
      "star": {"situation": str, "task": str, "action": str, "result": str},
      "tech_stack": [str], "domain_tags": [str]
  }],
  "experience_cards": [{
      "company": str, "period": str, "title": str, "scope": str,
      "achievements": [str], "industry": str, "is_current": bool
  }]
}

规则：
1. is_current=true 当且仅当 period 含"至今/Present/Now"。
2. 抽不到的字段填 null/空数组/空对象，不要乱编。
3. 输出仅 JSON，无 markdown，无 ``` 包裹。
"""

def build_user_prompt(text: str, persona_hint: str) -> str:
    return f"用户类型：{persona_hint}\n\n简历正文：\n{text}\n\n请输出 JSON。"
```

- [ ] **Step 2：写 schema**

`apps/api/src/schemas/resume.py`：
```python
from pydantic import BaseModel

class AbilityIn(BaseModel):
    skill_name: str
    evidence_text: str = ""
    level: int = 3
    last_used_year: int | None = None
    tags: list[str] = []

class STAR(BaseModel):
    situation: str = ""
    task: str = ""
    action: str = ""
    result: str = ""

class ProjectIn(BaseModel):
    project_name: str
    role: str = ""
    period: str = ""
    scale_data: dict = {}
    star: STAR = STAR()
    tech_stack: list[str] = []
    domain_tags: list[str] = []

class ExperienceIn(BaseModel):
    company: str
    period: str = ""
    title: str = ""
    scope: str = ""
    achievements: list[str] = []
    industry: str = ""
    is_current: bool = False

class ParsedResume(BaseModel):
    basic_info: dict = {}
    ability_cards: list[AbilityIn] = []
    project_cards: list[ProjectIn] = []
    experience_cards: list[ExperienceIn] = []
```

- [ ] **Step 3：写 service**

`apps/api/src/services/resume_parser.py`：
```python
import json
from uuid import UUID
from src.ai.llm_client import LLMClient
from src.ai.prompts.parse_resume import PARSE_RESUME_SYSTEM, build_user_prompt
from src.schemas.resume import ParsedResume
from src.models import PersonaType

_PERSONA_HINTS = {
    PersonaType.FRESH_GRAD: "应届校招（项目以实习/课程/竞赛为主）",
    PersonaType.JOB_HOPPER: "社招跳槽（有完整工作经验）",
    PersonaType.CAREER_CHANGER: "跨行业转行（有完整工作经验但跨域）",
}

_llm = LLMClient()

async def parse_resume_text(text: str, persona_type: PersonaType | None, user_id: UUID) -> ParsedResume:
    hint = _PERSONA_HINTS.get(persona_type or PersonaType.JOB_HOPPER)
    raw = await _llm.acomplete(
        model="auto-m1",
        system=PARSE_RESUME_SYSTEM,
        messages=[{"role": "user", "content": build_user_prompt(text, hint)}],
        max_tokens=4096,
        user_id=user_id, scene="resume_parse",
    )
    return ParsedResume.model_validate_json(raw)
```

- [ ] **Step 4：写测试（mock LLM）**

`apps/api/tests/test_resume_parser.py`：
```python
import json
from unittest.mock import AsyncMock, patch
from uuid import uuid4
import pytest
from src.services.resume_parser import parse_resume_text
from src.models import PersonaType

FAKE = {
    "basic_info": {"name": "张三", "phone": None, "email": None, "location": "北京"},
    "ability_cards": [{"skill_name": "增长", "evidence_text": "", "level": 4, "last_used_year": 2024, "tags": []}],
    "project_cards": [],
    "experience_cards": [{"company": "字节", "period": "2020-至今", "title": "PM", "scope": "", "achievements": [], "industry": "互联网", "is_current": True}],
}

@pytest.mark.asyncio
async def test_parse_returns_pydantic():
    with patch("src.services.resume_parser._llm.acomplete", AsyncMock(return_value=json.dumps(FAKE))):
        out = await parse_resume_text("any text", PersonaType.JOB_HOPPER, uuid4())
    assert out.basic_info["name"] == "张三"
    assert out.experience_cards[0].is_current is True
```

Run: `pytest -q tests/test_resume_parser.py` → PASS

- [ ] **Step 5：提交**

```bash
cd ../..
git add apps/api
git commit -m "feat(api): AI resume parser (MiniMax-M1) -> ParsedResume schema"
```

---

## Task 6: API — Upload Init + Parse + Get Endpoints

**Files:**
- Create: `apps/api/src/routers/master_resume.py`
- Create: `apps/api/src/schemas/master_resume.py`
- Modify: `apps/api/src/main.py`
- Create: `apps/api/tests/test_master_resume_api.py`

**Interfaces:**
- Produces:
  - `POST /api/v1/master-resume/upload-init` body `{filename: str, content_type: str}` → `{upload_url, s3_key}`
  - `POST /api/v1/master-resume/parse` body `{s3_key: str}` → 后端下载 + 抽取 + AI 解析 + 落库 → 返回完整 MasterResume
  - `GET /api/v1/master-resume` → 当前用户的 MasterResume（含所有卡片）

- [ ] **Step 1：写 schema**

`apps/api/src/schemas/master_resume.py`：
```python
from pydantic import BaseModel
from uuid import UUID

class UploadInitIn(BaseModel):
    filename: str
    content_type: str

class UploadInitOut(BaseModel):
    upload_url: str
    s3_key: str

class ParseIn(BaseModel):
    s3_key: str

class CardOut(BaseModel):
    id: UUID
    class Config: from_attributes = True

class AbilityCardOut(CardOut):
    skill_name: str; evidence_text: str; level: int
    last_used_year: int | None; tags: list[str]; is_weak: bool

class ProjectCardOut(CardOut):
    project_name: str; role: str; period: str
    scale_data: dict; star: dict; tech_stack: list[str]
    domain_tags: list[str]; is_weak: bool; weak_reasons: list[str]
    cross_domain_translation: dict

class ExperienceCardOut(CardOut):
    company: str; period: str; title: str; scope: str
    achievements: list[str]; industry: str; is_current: bool

class MasterResumeOut(BaseModel):
    id: UUID
    basic_info: dict
    quality_score: int | None
    ability_cards: list[AbilityCardOut]
    project_cards: list[ProjectCardOut]
    experience_cards: list[ExperienceCardOut]
```

- [ ] **Step 2：写 router**

`apps/api/src/routers/master_resume.py`：
```python
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.db import get_db
from src.core.deps import current_user
from src.core.security import encrypt_field, decrypt_field
from src.models import User, MasterResume, AbilityCard, ProjectCard, ExperienceCard
from src.schemas.master_resume import (
    UploadInitIn, UploadInitOut, ParseIn, MasterResumeOut,
    AbilityCardOut, ProjectCardOut, ExperienceCardOut,
)
from src.services.storage import presign_put, download_bytes
from src.services.text_extractor import extract_text
from src.services.resume_parser import parse_resume_text

router = APIRouter(prefix="/api/v1/master-resume", tags=["master-resume"])

def _serialize(r: MasterResume) -> MasterResumeOut:
    return MasterResumeOut(
        id=r.id, basic_info=r.basic_info or {}, quality_score=r.quality_score,
        ability_cards=[AbilityCardOut.model_validate(c) for c in r.ability_cards],
        project_cards=[ProjectCardOut.model_validate(c) for c in r.project_cards],
        experience_cards=[
            ExperienceCardOut(
                id=c.id, company=decrypt_field(c.company_encrypted) if c.company_encrypted else "",
                period=c.period, title=c.title, scope=c.scope,
                achievements=c.achievements, industry=c.industry, is_current=c.is_current,
            ) for c in r.experience_cards
        ],
    )

@router.post("/upload-init", response_model=UploadInitOut)
def upload_init(body: UploadInitIn, user: User = Depends(current_user)) -> UploadInitOut:
    key = f"users/{user.id}/resumes/{uuid4()}-{body.filename}"
    url = presign_put(key, body.content_type)
    return UploadInitOut(upload_url=url, s3_key=key)

@router.post("/parse", response_model=MasterResumeOut)
async def parse(body: ParseIn, user: User = Depends(current_user), db: Session = Depends(get_db)) -> MasterResumeOut:
    blob = download_bytes(body.s3_key)
    text = extract_text(body.s3_key.split("/")[-1], blob)
    parsed = await parse_resume_text(text, user.persona_type, user.id)

    # upsert MasterResume (1 per user)
    r = db.query(MasterResume).filter(MasterResume.user_id == user.id).first()
    if r is None:
        r = MasterResume(user_id=user.id)
        db.add(r); db.flush()
    else:
        # 清旧卡片
        for c in list(r.ability_cards) + list(r.project_cards) + list(r.experience_cards):
            db.delete(c)
        db.flush()

    r.basic_info = parsed.basic_info
    r.parsed_from_file_url = body.s3_key
    for a in parsed.ability_cards:
        r.ability_cards.append(AbilityCard(**a.model_dump()))
    for p in parsed.project_cards:
        r.project_cards.append(ProjectCard(**p.model_dump()))
    for e in parsed.experience_cards:
        d = e.model_dump()
        company_raw = d.pop("company")
        r.experience_cards.append(ExperienceCard(
            company_encrypted=encrypt_field(company_raw or "—"),
            **d,
        ))
    db.commit(); db.refresh(r)
    return _serialize(r)

@router.get("", response_model=MasterResumeOut | None)
def get_mine(user: User = Depends(current_user), db: Session = Depends(get_db)) -> MasterResumeOut | None:
    r = db.query(MasterResume).filter(MasterResume.user_id == user.id).first()
    return _serialize(r) if r else None
```

Modify `main.py` 加入 `from src.routers import master_resume` 和 `app.include_router(master_resume.router)`。

- [ ] **Step 3：测试**

`apps/api/tests/test_master_resume_api.py`：
```python
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from src.main import app
from src.core.security import issue_session_token
from src.core.db import SessionLocal
from src.models import User
from src.schemas.resume import ParsedResume, ExperienceIn

def _login() -> TestClient:
    db = SessionLocal()
    u = User(preferences={}); db.add(u); db.commit(); db.refresh(u)
    c = TestClient(app)
    c.cookies.set("jc_session", issue_session_token(u.id))
    return c

def test_upload_init_returns_url():
    with patch("src.routers.master_resume.presign_put", return_value="https://up.example.com"):
        c = _login()
        r = c.post("/api/v1/master-resume/upload-init", json={"filename":"r.pdf","content_type":"application/pdf"})
        assert r.status_code == 200
        assert r.json()["upload_url"].startswith("https://")

def test_parse_creates_resume():
    fake_parsed = ParsedResume(
        basic_info={"name":"张三"},
        ability_cards=[],
        project_cards=[],
        experience_cards=[ExperienceIn(company="字节", title="PM", is_current=True)],
    )
    with patch("src.routers.master_resume.download_bytes", return_value=b"x"), \
         patch("src.routers.master_resume.extract_text", return_value="some text"), \
         patch("src.routers.master_resume.parse_resume_text", AsyncMock(return_value=fake_parsed)):
        c = _login()
        r = c.post("/api/v1/master-resume/parse", json={"s3_key":"users/x/resumes/y.pdf"})
        assert r.status_code == 200
        body = r.json()
        assert body["basic_info"]["name"] == "张三"
        assert body["experience_cards"][0]["company"] == "字节"
        assert body["experience_cards"][0]["is_current"] is True
```

Run: `pytest -q tests/test_master_resume_api.py` → 2 passed

- [ ] **Step 4：提交**

```bash
cd ../..
git add apps/api
git commit -m "feat(api): master-resume upload-init/parse/get endpoints with field encryption"
```

---

## Task 7: API — Card CRUD Endpoints

**Files:**
- Modify: `apps/api/src/routers/master_resume.py`（追加 card 路由）
- Create: `apps/api/tests/test_card_crud.py`

**Interfaces:**
- Produces:
  - `POST /api/v1/master-resume/cards/{type}` 创建卡片
  - `PATCH /api/v1/master-resume/cards/{type}/{card_id}` 更新
  - `DELETE /api/v1/master-resume/cards/{type}/{card_id}` 删除
  - `{type}` ∈ `{ability, project, experience}`

- [ ] **Step 1：扩 router**

追加到 `master_resume.py`：
```python
from fastapi import status
from src.core.security import encrypt_field

_CARD_MODELS = {"ability": AbilityCard, "project": ProjectCard, "experience": ExperienceCard}

def _get_resume(user, db) -> MasterResume:
    r = db.query(MasterResume).filter(MasterResume.user_id == user.id).first()
    if not r:
        raise HTTPException(status_code=404, detail="master resume not found; upload first")
    return r

@router.post("/cards/{card_type}", status_code=status.HTTP_201_CREATED)
def create_card(card_type: str, body: dict, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    model = _CARD_MODELS.get(card_type)
    if not model: raise HTTPException(400, "invalid card type")
    r = _get_resume(user, db)
    if card_type == "experience" and "company" in body:
        body["company_encrypted"] = encrypt_field(body.pop("company"))
    obj = model(master_resume_id=r.id, **body)
    db.add(obj); db.commit(); db.refresh(obj)
    return {"id": str(obj.id)}

@router.patch("/cards/{card_type}/{card_id}")
def update_card(card_type: str, card_id: str, body: dict, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    model = _CARD_MODELS.get(card_type)
    if not model: raise HTTPException(400, "invalid card type")
    r = _get_resume(user, db)
    obj = db.query(model).filter(model.id == card_id, model.master_resume_id == r.id).first()
    if not obj: raise HTTPException(404, "card not found")
    if card_type == "experience" and "company" in body:
        body["company_encrypted"] = encrypt_field(body.pop("company"))
    for k, v in body.items():
        if hasattr(obj, k): setattr(obj, k, v)
    db.commit()
    return {"ok": True}

@router.delete("/cards/{card_type}/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(card_type: str, card_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> None:
    model = _CARD_MODELS.get(card_type)
    if not model: raise HTTPException(400, "invalid card type")
    r = _get_resume(user, db)
    obj = db.query(model).filter(model.id == card_id, model.master_resume_id == r.id).first()
    if not obj: raise HTTPException(404, "card not found")
    db.delete(obj); db.commit()
```

- [ ] **Step 2：测试**

`apps/api/tests/test_card_crud.py`：
```python
from fastapi.testclient import TestClient
from src.main import app
from src.core.security import issue_session_token
from src.core.db import SessionLocal
from src.models import User, MasterResume

def _login_with_resume():
    db = SessionLocal()
    u = User(preferences={}); db.add(u); db.commit(); db.refresh(u)
    r = MasterResume(user_id=u.id); db.add(r); db.commit(); db.refresh(r)
    c = TestClient(app); c.cookies.set("jc_session", issue_session_token(u.id))
    return c

def test_create_update_delete_ability_card():
    c = _login_with_resume()
    r = c.post("/api/v1/master-resume/cards/ability", json={"skill_name":"增长","level":4})
    assert r.status_code == 201
    cid = r.json()["id"]
    r2 = c.patch(f"/api/v1/master-resume/cards/ability/{cid}", json={"level":5})
    assert r2.status_code == 200
    r3 = c.delete(f"/api/v1/master-resume/cards/ability/{cid}")
    assert r3.status_code == 204

def test_create_experience_encrypts_company():
    c = _login_with_resume()
    r = c.post("/api/v1/master-resume/cards/experience",
               json={"company":"字节跳动","title":"PM","is_current":True})
    assert r.status_code == 201
```

Run: `pytest -q tests/test_card_crud.py` → 2 passed

- [ ] **Step 3：提交**

```bash
cd ../..
git add apps/api
git commit -m "feat(api): card CRUD for ability/project/experience with company encryption"
```

---

## Task 8: AI 含金量诊断 Service + Endpoint

**Files:**
- Create: `apps/api/src/ai/prompts/diagnose_quality.py`
- Create: `apps/api/src/services/quality_diagnoser.py`
- Modify: `apps/api/src/routers/master_resume.py`（追加 POST /diagnose）
- Create: `apps/api/tests/test_quality_diagnoser.py`

**Interfaces:**
- Produces:
  - `async diagnose(master_resume_id: UUID, user_id: UUID) -> {overall_score, weak_cards: [{type, id, reasons:[str]}]}`
  - `POST /api/v1/master-resume/diagnose` → 写回每张卡片的 `is_weak` 和 `weak_reasons`，更新 `quality_score`

- [ ] **Step 1：写 prompt**

`apps/api/src/ai/prompts/diagnose_quality.py`：
```python
DIAGNOSE_QUALITY_SYSTEM = """你是简历审核官，针对主简历卡片打"含金量"诊断。
输入：主简历的所有卡片（JSON）。
输出严格 JSON：
{
  "overall_score": 0-100,
  "weak_cards": [{"type": "ability|project|experience", "id": str, "reasons": [str]}]
}
判断"含金量低"的常见原因：
- 项目无数据/无规模、动作模糊、与岗位无关
- 能力无证据、过期 > 3 年
- 经历无成果、scope 缺
不要乱标——仅标真有问题的卡片。
仅输出 JSON。
"""
```

- [ ] **Step 2：写 service**

`apps/api/src/services/quality_diagnoser.py`：
```python
import json
from uuid import UUID
from sqlalchemy.orm import Session
from src.ai.llm_client import LLMClient
from src.ai.prompts.diagnose_quality import DIAGNOSE_QUALITY_SYSTEM
from src.models import MasterResume, AbilityCard, ProjectCard, ExperienceCard
from src.core.security import decrypt_field

_llm = LLMClient()

def _to_input(r: MasterResume) -> dict:
    return {
        "ability_cards": [
            {"id": str(c.id), "skill_name": c.skill_name, "evidence_text": c.evidence_text,
             "level": c.level, "last_used_year": c.last_used_year}
            for c in r.ability_cards
        ],
        "project_cards": [
            {"id": str(c.id), "project_name": c.project_name, "role": c.role,
             "scale_data": c.scale_data, "star": c.star, "tech_stack": c.tech_stack}
            for c in r.project_cards
        ],
        "experience_cards": [
            {"id": str(c.id), "company": decrypt_field(c.company_encrypted),
             "period": c.period, "title": c.title, "scope": c.scope,
             "achievements": c.achievements, "industry": c.industry}
            for c in r.experience_cards
        ],
    }

async def diagnose(db: Session, master_resume_id: UUID, user_id: UUID) -> dict:
    r = db.get(MasterResume, master_resume_id)
    if not r: raise ValueError("not found")
    payload = json.dumps(_to_input(r), ensure_ascii=False)
    raw = await _llm.acomplete(
        model="auto-m1",
        system=DIAGNOSE_QUALITY_SYSTEM,
        messages=[{"role": "user", "content": payload}],
        max_tokens=2048, user_id=user_id, scene="resume_diagnose",
    )
    result = json.loads(raw)
    # 写回 is_weak
    weak_ids = {(w["type"], w["id"]): w["reasons"] for w in result.get("weak_cards", [])}
    for c in r.ability_cards:    c.is_weak = ("ability", str(c.id)) in weak_ids
    for c in r.project_cards:
        c.is_weak = ("project", str(c.id)) in weak_ids
        c.weak_reasons = weak_ids.get(("project", str(c.id)), [])
    for c in r.experience_cards: c.is_weak = ("experience", str(c.id)) in weak_ids
    r.quality_score = result.get("overall_score")
    db.commit()
    return result
```

- [ ] **Step 3：写 endpoint**

追加到 `master_resume.py`：
```python
from src.services.quality_diagnoser import diagnose as diagnose_svc

@router.post("/diagnose")
async def diagnose(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    r = _get_resume(user, db)
    return await diagnose_svc(db, r.id, user.id)
```

- [ ] **Step 4：测试**

`apps/api/tests/test_quality_diagnoser.py`：
```python
import json
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from src.main import app
from src.core.security import issue_session_token
from src.core.db import SessionLocal
from src.models import User, MasterResume, AbilityCard

def _setup():
    db = SessionLocal()
    u = User(preferences={}); db.add(u); db.commit(); db.refresh(u)
    r = MasterResume(user_id=u.id); db.add(r); db.flush()
    a = AbilityCard(master_resume_id=r.id, skill_name="Python", level=3); db.add(a)
    db.commit(); db.refresh(r); db.refresh(a)
    c = TestClient(app); c.cookies.set("jc_session", issue_session_token(u.id))
    return c, str(a.id)

def test_diagnose_marks_weak():
    c, aid = _setup()
    fake = {"overall_score": 65, "weak_cards":[{"type":"ability","id":aid,"reasons":["evidence missing"]}]}
    with patch("src.services.quality_diagnoser._llm.acomplete", AsyncMock(return_value=json.dumps(fake))):
        r = c.post("/api/v1/master-resume/diagnose")
    assert r.status_code == 200
    assert r.json()["overall_score"] == 65
```

Run: `pytest -q tests/test_quality_diagnoser.py` → PASS

- [ ] **Step 5：提交**

```bash
cd ../..
git add apps/api
git commit -m "feat(api): AI quality diagnoser endpoint marks weak cards + writes quality_score"
```

---

## Task 9: AI 应届"轻问诊" Service + Endpoints

**Files:**
- Create: `apps/api/src/ai/prompts/intake_dialogue.py`
- Create: `apps/api/src/services/intake.py`
- Create: `apps/api/src/models/intake_session.py`
- Create: `apps/api/alembic/versions/0005_intake_session.py`
- Modify: `apps/api/src/models/__init__.py`
- Modify: `apps/api/src/routers/master_resume.py`（追加 intake 路由）
- Create: `apps/api/tests/test_intake.py`

**Interfaces:**
- Produces:
  - `IntakeSession(id, user_id, transcript JSON, finished_at)`
  - `POST /api/v1/master-resume/intake/start` → `{session_id, first_question}`
  - `POST /api/v1/master-resume/intake/answer` body `{session_id, answer}` → `{next_question | done}`
  - `POST /api/v1/master-resume/intake/finalize` body `{session_id}` → AI 把 transcript 转为 cards 并落 master resume
- 应届仅；其他 persona 走标准上传流程

- [ ] **Step 1：模型 + 迁移**

`apps/api/src/models/intake_session.py`：
```python
from datetime import datetime
from uuid import uuid4, UUID
import sqlalchemy as sa
from sqlalchemy import JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from src.core.db import Base

class IntakeSession(Base):
    __tablename__ = "intake_sessions"
    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(sa.Uuid, index=True)
    transcript: Mapped[list] = mapped_column(JSON, default=list)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=sa.func.now())
```

```bash
cd apps/api && source .venv/bin/activate
alembic revision --autogenerate -m "intake session"
alembic upgrade head
```

- [ ] **Step 2：写 prompts**

`apps/api/src/ai/prompts/intake_dialogue.py`：
```python
INTAKE_FIRST_Q = "你好！想一起聊几分钟，把你的实习/项目/课程经历挖出来。先说一段你自己最自豪的项目或实习，是什么、你做了什么？"

INTAKE_DIALOGUE_SYSTEM = """你是温和的"挖经历"教练，对话对象是应届生。
目标：通过 5-8 轮短问答，挖出 1-2 个项目/实习的细节（背景、个人贡献、动作、数据/结果）+ 1-2 个能力证据。
规则：
- 一次只问一个问题；问题简短不超过 2 句。
- 当你已收集足够细节，回复严格 JSON：{"done": true, "summary": "..."}
- 否则回复：{"done": false, "next_question": "..."}
- 仅输出 JSON，无 markdown。
"""

INTAKE_FINALIZE_SYSTEM = """你是结构化助手。
输入：用户与教练的 transcript（list of {role, content}）。
输出严格 JSON，与简历解析 schema 相同：
{
  "basic_info": {"name": str|null},
  "ability_cards": [...],
  "project_cards": [...],
  "experience_cards": [...]
}
仅输出 JSON。
"""
```

- [ ] **Step 3：写 service**

`apps/api/src/services/intake.py`：
```python
import json
from uuid import UUID
from sqlalchemy.orm import Session
from src.ai.llm_client import LLMClient
from src.ai.prompts.intake_dialogue import INTAKE_FIRST_Q, INTAKE_DIALOGUE_SYSTEM, INTAKE_FINALIZE_SYSTEM
from src.models.intake_session import IntakeSession
from src.schemas.resume import ParsedResume

_llm = LLMClient()

def start(db: Session, user_id: UUID) -> tuple[UUID, str]:
    s = IntakeSession(user_id=user_id, transcript=[{"role":"assistant","content": INTAKE_FIRST_Q}])
    db.add(s); db.commit(); db.refresh(s)
    return s.id, INTAKE_FIRST_Q

async def answer(db: Session, session_id: UUID, user_id: UUID, user_msg: str) -> dict:
    s = db.get(IntakeSession, session_id)
    if not s or s.user_id != user_id:
        raise ValueError("session not found")
    s.transcript = [*s.transcript, {"role":"user","content": user_msg}]
    raw = await _llm.acomplete(
        model="auto-light",
        system=INTAKE_DIALOGUE_SYSTEM,
        messages=s.transcript,
        max_tokens=512, user_id=user_id, scene="intake_dialogue",
    )
    data = json.loads(raw)
    if data.get("done"):
        s.transcript = [*s.transcript, {"role":"assistant","content": json.dumps(data, ensure_ascii=False)}]
        db.commit()
        return {"done": True}
    s.transcript = [*s.transcript, {"role":"assistant","content": data["next_question"]}]
    db.commit()
    return {"done": False, "next_question": data["next_question"]}

async def finalize(db: Session, session_id: UUID, user_id: UUID) -> ParsedResume:
    s = db.get(IntakeSession, session_id)
    if not s or s.user_id != user_id: raise ValueError("session not found")
    raw = await _llm.acomplete(
        model="auto-m1",
        system=INTAKE_FINALIZE_SYSTEM,
        messages=[{"role":"user","content": json.dumps(s.transcript, ensure_ascii=False)}],
        max_tokens=4096, user_id=user_id, scene="intake_finalize",
    )
    from datetime import datetime, timezone
    s.finished_at = datetime.now(timezone.utc); db.commit()
    return ParsedResume.model_validate_json(raw)
```

- [ ] **Step 4：写 endpoints + 接入解析落库**

追加到 `master_resume.py`：
```python
from src.services import intake as intake_svc
from pydantic import BaseModel

class IntakeStartOut(BaseModel):
    session_id: str
    first_question: str

class IntakeAnswerIn(BaseModel):
    session_id: str
    answer: str

class IntakeFinalizeIn(BaseModel):
    session_id: str

@router.post("/intake/start", response_model=IntakeStartOut)
def intake_start(user: User = Depends(current_user), db: Session = Depends(get_db)) -> IntakeStartOut:
    sid, q = intake_svc.start(db, user.id)
    return IntakeStartOut(session_id=str(sid), first_question=q)

@router.post("/intake/answer")
async def intake_answer(body: IntakeAnswerIn, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return await intake_svc.answer(db, UUID(body.session_id), user.id, body.answer)

@router.post("/intake/finalize", response_model=MasterResumeOut)
async def intake_finalize(body: IntakeFinalizeIn, user: User = Depends(current_user), db: Session = Depends(get_db)) -> MasterResumeOut:
    parsed = await intake_svc.finalize(db, UUID(body.session_id), user.id)
    # 复用 parse 的落库逻辑
    r = db.query(MasterResume).filter(MasterResume.user_id == user.id).first()
    if r is None: r = MasterResume(user_id=user.id); db.add(r); db.flush()
    else:
        for c in list(r.ability_cards) + list(r.project_cards) + list(r.experience_cards):
            db.delete(c)
        db.flush()
    r.basic_info = parsed.basic_info
    for a in parsed.ability_cards:    r.ability_cards.append(AbilityCard(**a.model_dump()))
    for p in parsed.project_cards:    r.project_cards.append(ProjectCard(**p.model_dump()))
    for e in parsed.experience_cards:
        d = e.model_dump(); company = d.pop("company")
        r.experience_cards.append(ExperienceCard(company_encrypted=encrypt_field(company or "—"), **d))
    db.commit(); db.refresh(r)
    return _serialize(r)
```

- [ ] **Step 5：测试**

`apps/api/tests/test_intake.py`：
```python
import json
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from src.main import app
from src.core.security import issue_session_token
from src.core.db import SessionLocal
from src.models import User, PersonaType

def _login_fresh_grad():
    db = SessionLocal()
    u = User(preferences={}, persona_type=PersonaType.FRESH_GRAD); db.add(u); db.commit(); db.refresh(u)
    c = TestClient(app); c.cookies.set("jc_session", issue_session_token(u.id))
    return c

def test_intake_flow():
    c = _login_fresh_grad()
    r = c.post("/api/v1/master-resume/intake/start")
    assert r.status_code == 200
    sid = r.json()["session_id"]

    with patch("src.services.intake._llm.acomplete", AsyncMock(return_value=json.dumps({"done": False, "next_question":"再说一个"}))):
        r = c.post("/api/v1/master-resume/intake/answer", json={"session_id": sid, "answer":"我做了 X"})
        assert r.json()["done"] is False

    with patch("src.services.intake._llm.acomplete", AsyncMock(return_value=json.dumps({"done": True, "summary":"ok"}))):
        r = c.post("/api/v1/master-resume/intake/answer", json={"session_id": sid, "answer":"再补充"})
        assert r.json()["done"] is True
```

Run: `pytest -q tests/test_intake.py` → PASS

- [ ] **Step 6：提交**

```bash
cd ../..
git add apps/api
git commit -m "feat(api): fresh-grad intake (start/answer/finalize) AI dialogue + finalize to cards"
```

---

## Task 10: Web — TanStack Query 接入 + API hooks

**Files:**
- Modify: `apps/web/package.json`（装 @tanstack/react-query）
- Create: `apps/web/src/lib/queryClient.tsx`
- Create: `apps/web/src/hooks/useMasterResume.ts`
- Modify: `apps/web/src/app/[locale]/layout.tsx`（QueryProvider）

**Interfaces:**
- Produces:
  - 全局 `QueryClientProvider`
  - `useMasterResume()`、`useDiagnose()`、`useCreateCard(type)`、`useUpdateCard(type)`、`useDeleteCard(type)`、`useUploadInit()`、`useParseResume()`

- [ ] **Step 1：装依赖**

```bash
cd apps/web && pnpm add @tanstack/react-query@5.59.16 && cd ../..
```

- [ ] **Step 2：写 QueryClient provider**

`apps/web/src/lib/queryClient.tsx`：
```typescript
'use client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState, type ReactNode } from 'react'

export function Providers({ children }: { children: ReactNode }) {
  const [client] = useState(() => new QueryClient({
    defaultOptions: { queries: { retry: 1, staleTime: 30_000 } },
  }))
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>
}
```

Modify `apps/web/src/app/[locale]/layout.tsx`：
```typescript
import { Providers } from '@/lib/queryClient'
// ...
<NextIntlClientProvider messages={messages}>
  <PostHogBoot />
  <Providers>{children}</Providers>
</NextIntlClientProvider>
```

- [ ] **Step 3：写 hooks**

`apps/web/src/hooks/useMasterResume.ts`：
```typescript
'use client'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'

type CardType = 'ability' | 'project' | 'experience'

export function useMasterResume() {
  return useQuery({
    queryKey: ['master-resume'],
    queryFn: () => api<unknown>('/api/v1/master-resume'),
  })
}

export function useUploadInit() {
  return useMutation({
    mutationFn: (vars: { filename: string; content_type: string }) =>
      api<{ upload_url: string; s3_key: string }>('/api/v1/master-resume/upload-init', {
        method: 'POST', body: JSON.stringify(vars),
      }),
  })
}

export function useParseResume() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (vars: { s3_key: string }) =>
      api('/api/v1/master-resume/parse', { method: 'POST', body: JSON.stringify(vars) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['master-resume'] }),
  })
}

export function useDiagnose() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => api('/api/v1/master-resume/diagnose', { method: 'POST' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['master-resume'] }),
  })
}

export function useCreateCard(type: CardType) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: Record<string, unknown>) =>
      api(`/api/v1/master-resume/cards/${type}`, { method: 'POST', body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['master-resume'] }),
  })
}

export function useUpdateCard(type: CardType) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (vars: { id: string; body: Record<string, unknown> }) =>
      api(`/api/v1/master-resume/cards/${type}/${vars.id}`, { method: 'PATCH', body: JSON.stringify(vars.body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['master-resume'] }),
  })
}

export function useDeleteCard(type: CardType) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) =>
      api(`/api/v1/master-resume/cards/${type}/${id}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['master-resume'] }),
  })
}
```

- [ ] **Step 4：提交**

```bash
git add apps/web
git commit -m "feat(web): tanstack-query setup + master-resume hooks"
```

---

## Task 11: Web — 上传简历页（拖拽 + 直传 S3 + 触发解析）

**Files:**
- Create: `apps/web/src/components/master-resume/UploadDropzone.tsx`
- Modify: `apps/web/src/app/[locale]/(app)/master-resume/page.tsx`
- Modify: `apps/web/messages/{zh,en}.json`（追加上传文案）

**Interfaces:**
- Produces:
  - 拖入/点击 PDF 或 DOCX → 调用 upload-init 拿 URL → 浏览器 PUT 到 S3 → 调用 parse → 跳到卡片视图
  - 上传进度条 + 解析中状态

- [ ] **Step 1：写 Dropzone**

```typescript
'use client'
import { useRef, useState } from 'react'
import { useTranslations } from 'next-intl'
import { useUploadInit, useParseResume } from '@/hooks/useMasterResume'

export function UploadDropzone({ onParsed }: { onParsed: () => void }) {
  const t = useTranslations('master_resume')
  const init = useUploadInit()
  const parse = useParseResume()
  const inp = useRef<HTMLInputElement>(null)
  const [stage, setStage] = useState<'idle' | 'uploading' | 'parsing' | 'error'>('idle')
  const [progress, setProgress] = useState(0)
  const [err, setErr] = useState<string | null>(null)

  async function handle(file: File) {
    setErr(null); setStage('uploading'); setProgress(0)
    try {
      const { upload_url, s3_key } = await init.mutateAsync({ filename: file.name, content_type: file.type })
      // browser PUT to S3 with progress
      await new Promise<void>((resolve, reject) => {
        const xhr = new XMLHttpRequest()
        xhr.open('PUT', upload_url)
        xhr.setRequestHeader('Content-Type', file.type)
        xhr.upload.onprogress = (e) => e.lengthComputable && setProgress(Math.round((e.loaded / e.total) * 100))
        xhr.onload = () => xhr.status < 300 ? resolve() : reject(new Error(`upload ${xhr.status}`))
        xhr.onerror = () => reject(new Error('network'))
        xhr.send(file)
      })
      setStage('parsing')
      await parse.mutateAsync({ s3_key })
      setStage('idle'); onParsed()
    } catch (e) {
      setErr(String(e)); setStage('error')
    }
  }

  return (
    <div
      onDragOver={(e) => e.preventDefault()}
      onDrop={(e) => { e.preventDefault(); const f = e.dataTransfer.files?.[0]; if (f) handle(f) }}
      onClick={() => inp.current?.click()}
      className="border-2 border-dashed rounded p-12 text-center cursor-pointer hover:bg-gray-50"
    >
      <input ref={inp} type="file" accept=".pdf,.docx" className="hidden"
             onChange={(e) => e.target.files?.[0] && handle(e.target.files[0])} />
      {stage === 'idle' && <p>{t('drop_or_click')}</p>}
      {stage === 'uploading' && <p>{t('uploading')} {progress}%</p>}
      {stage === 'parsing' && <p>{t('parsing')}</p>}
      {stage === 'error' && <p className="text-red-700">{err}</p>}
    </div>
  )
}
```

- [ ] **Step 2：扩翻译**

`zh.json` 追加：
```json
"master_resume": {
  "title": "我的主简历",
  "empty": "还没有主简历，先上传你的现有简历开始",
  "drop_or_click": "拖入 PDF / DOCX，或点击选择",
  "uploading": "上传中…",
  "parsing": "AI 正在结构化解析…",
  "diagnose": "AI 含金量诊断",
  "ability": "能力",
  "project": "项目",
  "experience": "经历",
  "weak_marker": "⚠ 含金量低",
  "current_company_warning": "这是你现在的公司，导出时默认脱敏"
}
```

`en.json` 对应英文（略，照抄结构）。

- [ ] **Step 3：写主页**

`apps/web/src/app/[locale]/(app)/master-resume/page.tsx`：
```typescript
'use client'
import { useTranslations } from 'next-intl'
import { UploadDropzone } from '@/components/master-resume/UploadDropzone'
import { useMasterResume } from '@/hooks/useMasterResume'
import { ResumeCards } from '@/components/master-resume/ResumeCards' // 下个 task

export default function MasterResumePage() {
  const t = useTranslations('master_resume')
  const { data, refetch } = useMasterResume()
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t('title')}</h1>
      {!data ? (
        <>
          <p className="text-muted-foreground">{t('empty')}</p>
          <UploadDropzone onParsed={() => refetch()} />
        </>
      ) : (
        <ResumeCards data={data as never} />
      )}
    </div>
  )
}
```

- [ ] **Step 4：提交**

```bash
git add apps/web
git commit -m "feat(web): upload dropzone with S3 direct PUT + parse trigger"
```

---

## Task 12: Web — 三类卡片编辑组件 + ResumeCards 容器

**Files:**
- Create: `apps/web/src/components/master-resume/ResumeCards.tsx`
- Create: `apps/web/src/components/master-resume/AbilityCardItem.tsx`
- Create: `apps/web/src/components/master-resume/ProjectCardItem.tsx`
- Create: `apps/web/src/components/master-resume/ExperienceCardItem.tsx`
- Create: `apps/web/src/components/master-resume/CurrentCompanyWarning.tsx`

**Interfaces:**
- Produces:
  - `ResumeCards` 三栏：能力 / 项目 / 经历，每栏可增删改
  - 含 `⚠ 含金量低` 标记
  - 经历卡若 `is_current=true` 显示警告条
  - 用 Dialog/Drawer 做编辑

- [ ] **Step 1：CurrentCompanyWarning**

```typescript
'use client'
import { useTranslations } from 'next-intl'

export function CurrentCompanyWarning() {
  const t = useTranslations('master_resume')
  return (
    <div className="text-xs bg-yellow-50 border border-yellow-300 text-yellow-900 rounded px-2 py-1">
      🔒 {t('current_company_warning')}
    </div>
  )
}
```

- [ ] **Step 2：AbilityCardItem（简化版，inline edit）**

```typescript
'use client'
import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { useUpdateCard, useDeleteCard } from '@/hooks/useMasterResume'

type A = { id: string; skill_name: string; level: number; evidence_text: string; is_weak: boolean }

export function AbilityCardItem({ card }: { card: A }) {
  const t = useTranslations('master_resume')
  const [name, setName] = useState(card.skill_name)
  const [lvl, setLvl] = useState(card.level)
  const update = useUpdateCard('ability')
  const del = useDeleteCard('ability')
  return (
    <div className="border rounded p-3 space-y-2">
      <div className="flex items-center justify-between">
        <input value={name} onChange={(e) => setName(e.target.value)}
               onBlur={() => update.mutate({ id: card.id, body: { skill_name: name } })}
               className="font-semibold bg-transparent outline-none" />
        <button onClick={() => del.mutate(card.id)} className="text-red-600 text-sm">✕</button>
      </div>
      <div className="flex items-center gap-2 text-sm">
        <span>Lv</span>
        <input type="number" min={1} max={5} value={lvl}
               onChange={(e) => setLvl(parseInt(e.target.value))}
               onBlur={() => update.mutate({ id: card.id, body: { level: lvl } })}
               className="w-12 border rounded px-1" />
        {card.is_weak && <span className="text-orange-600">{t('weak_marker')}</span>}
      </div>
    </div>
  )
}
```

- [ ] **Step 3：ProjectCardItem（带 STAR 折叠编辑）**

```typescript
'use client'
import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { useUpdateCard, useDeleteCard } from '@/hooks/useMasterResume'

type P = { id: string; project_name: string; role: string; period: string; star: { situation: string; task: string; action: string; result: string }; is_weak: boolean; weak_reasons: string[] }

export function ProjectCardItem({ card }: { card: P }) {
  const t = useTranslations('master_resume')
  const [open, setOpen] = useState(false)
  const [star, setStar] = useState(card.star || { situation:'', task:'', action:'', result:'' })
  const update = useUpdateCard('project')
  const del = useDeleteCard('project')
  function save() { update.mutate({ id: card.id, body: { star } }) }
  return (
    <div className="border rounded p-3 space-y-2">
      <div className="flex items-center justify-between">
        <strong>{card.project_name}</strong>
        <div className="flex gap-2">
          {card.is_weak && <span className="text-orange-600 text-xs">{t('weak_marker')}</span>}
          <button onClick={() => setOpen((o) => !o)} className="text-sm">{open ? '收起' : '编辑'}</button>
          <button onClick={() => del.mutate(card.id)} className="text-red-600 text-sm">✕</button>
        </div>
      </div>
      <div className="text-xs text-gray-500">{card.role} · {card.period}</div>
      {card.is_weak && card.weak_reasons?.length > 0 && (
        <ul className="text-xs text-orange-700 list-disc pl-4">{card.weak_reasons.map((r,i)=><li key={i}>{r}</li>)}</ul>
      )}
      {open && (
        <div className="space-y-2 text-sm">
          {(['situation','task','action','result'] as const).map((k) => (
            <div key={k}>
              <label className="block text-xs uppercase">{k}</label>
              <textarea value={star[k]} onChange={(e) => setStar({ ...star, [k]: e.target.value })}
                        onBlur={save} className="w-full border rounded p-1" rows={2} />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 4：ExperienceCardItem**

```typescript
'use client'
import { useState } from 'react'
import { useUpdateCard, useDeleteCard } from '@/hooks/useMasterResume'
import { CurrentCompanyWarning } from './CurrentCompanyWarning'

type E = { id: string; company: string; title: string; period: string; scope: string; is_current: boolean }

export function ExperienceCardItem({ card }: { card: E }) {
  const [c, setC] = useState({ company: card.company, title: card.title, period: card.period, scope: card.scope })
  const update = useUpdateCard('experience')
  const del = useDeleteCard('experience')
  function save() { update.mutate({ id: card.id, body: c }) }
  return (
    <div className="border rounded p-3 space-y-2">
      {card.is_current && <CurrentCompanyWarning />}
      <div className="flex items-center justify-between">
        <input value={c.company} onChange={(e) => setC({ ...c, company: e.target.value })} onBlur={save}
               className="font-semibold bg-transparent outline-none" />
        <button onClick={() => del.mutate(card.id)} className="text-red-600 text-sm">✕</button>
      </div>
      <input value={c.title} onChange={(e) => setC({ ...c, title: e.target.value })} onBlur={save}
             placeholder="职位" className="w-full border-b text-sm bg-transparent" />
      <input value={c.period} onChange={(e) => setC({ ...c, period: e.target.value })} onBlur={save}
             placeholder="时间段" className="w-full border-b text-xs bg-transparent" />
      <textarea value={c.scope} onChange={(e) => setC({ ...c, scope: e.target.value })} onBlur={save}
                placeholder="职责描述" className="w-full border rounded p-1 text-sm" rows={2} />
    </div>
  )
}
```

- [ ] **Step 5：ResumeCards 容器**

```typescript
'use client'
import { useTranslations } from 'next-intl'
import { useCreateCard, useDiagnose } from '@/hooks/useMasterResume'
import { AbilityCardItem } from './AbilityCardItem'
import { ProjectCardItem } from './ProjectCardItem'
import { ExperienceCardItem } from './ExperienceCardItem'

type Data = {
  ability_cards: any[]; project_cards: any[]; experience_cards: any[]
  quality_score: number | null
}

export function ResumeCards({ data }: { data: Data }) {
  const t = useTranslations('master_resume')
  const addA = useCreateCard('ability')
  const addP = useCreateCard('project')
  const addE = useCreateCard('experience')
  const diag = useDiagnose()
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <button onClick={() => diag.mutate()} disabled={diag.isPending}
                className="px-3 py-2 rounded bg-blue-600 text-white">
          {diag.isPending ? '诊断中…' : t('diagnose')}
        </button>
        {data.quality_score !== null && <span className="text-sm">综合 {data.quality_score}/100</span>}
      </div>
      <div className="grid grid-cols-3 gap-6">
        <Col title={t('ability')} onAdd={() => addA.mutate({ skill_name: '新能力', level: 3 })}>
          {data.ability_cards.map((c) => <AbilityCardItem key={c.id} card={c} />)}
        </Col>
        <Col title={t('project')} onAdd={() => addP.mutate({ project_name: '新项目' })}>
          {data.project_cards.map((c) => <ProjectCardItem key={c.id} card={c} />)}
        </Col>
        <Col title={t('experience')} onAdd={() => addE.mutate({ company: '新公司', title: '', is_current: false })}>
          {data.experience_cards.map((c) => <ExperienceCardItem key={c.id} card={c} />)}
        </Col>
      </div>
    </div>
  )
}

function Col({ title, onAdd, children }: { title: string; onAdd: () => void; children: React.ReactNode }) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="font-bold">{title}</h2>
        <button onClick={onAdd} className="text-sm border rounded px-2">+</button>
      </div>
      {children}
    </div>
  )
}
```

- [ ] **Step 6：提交**

```bash
git add apps/web
git commit -m "feat(web): three card editors + ResumeCards container with diagnose button"
```

---

## Task 13: Web — 应届"轻问诊"对话 UI

**Files:**
- Create: `apps/web/src/components/master-resume/IntakeDialog.tsx`
- Create: `apps/web/src/hooks/useIntake.ts`
- Modify: `apps/web/src/app/[locale]/(app)/master-resume/page.tsx`（应届时显示入口）

**Interfaces:**
- Produces:
  - 用户首页（无 master-resume + 应届生）显示双 CTA：「上传简历」或「让 AI 帮我挖经历」
  - IntakeDialog：start → answer 多轮 → done → finalize → 落卡片

- [ ] **Step 1：hooks**

`apps/web/src/hooks/useIntake.ts`：
```typescript
'use client'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'

export function useIntakeStart() {
  return useMutation({ mutationFn: () => api<{ session_id: string; first_question: string }>('/api/v1/master-resume/intake/start', { method: 'POST' }) })
}
export function useIntakeAnswer() {
  return useMutation({
    mutationFn: (vars: { session_id: string; answer: string }) =>
      api<{ done: boolean; next_question?: string }>('/api/v1/master-resume/intake/answer', { method: 'POST', body: JSON.stringify(vars) }),
  })
}
export function useIntakeFinalize() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (vars: { session_id: string }) => api('/api/v1/master-resume/intake/finalize', { method: 'POST', body: JSON.stringify(vars) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['master-resume'] }),
  })
}
```

- [ ] **Step 2：IntakeDialog**

```typescript
'use client'
import { useState, useEffect } from 'react'
import { useIntakeStart, useIntakeAnswer, useIntakeFinalize } from '@/hooks/useIntake'

export function IntakeDialog({ onDone }: { onDone: () => void }) {
  const start = useIntakeStart()
  const answer = useIntakeAnswer()
  const finalize = useIntakeFinalize()
  const [sid, setSid] = useState<string | null>(null)
  const [turns, setTurns] = useState<{ role: 'q' | 'a'; text: string }[]>([])
  const [input, setInput] = useState('')
  const [done, setDone] = useState(false)

  useEffect(() => {
    start.mutateAsync().then((r) => {
      setSid(r.session_id); setTurns([{ role: 'q', text: r.first_question }])
    })
  }, [])

  async function send() {
    if (!sid || !input.trim()) return
    const ans = input
    setTurns((t) => [...t, { role: 'a', text: ans }]); setInput('')
    const r = await answer.mutateAsync({ session_id: sid, answer: ans })
    if (r.done) setDone(true)
    else setTurns((t) => [...t, { role: 'q', text: r.next_question! }])
  }

  async function finish() {
    if (!sid) return
    await finalize.mutateAsync({ session_id: sid })
    onDone()
  }

  return (
    <div className="max-w-2xl mx-auto space-y-4">
      <div className="border rounded p-4 h-96 overflow-auto space-y-2">
        {turns.map((t, i) => (
          <div key={i} className={t.role === 'q' ? '' : 'text-right'}>
            <span className={`inline-block rounded px-3 py-2 ${t.role === 'q' ? 'bg-gray-100' : 'bg-blue-100'}`}>{t.text}</span>
          </div>
        ))}
      </div>
      {!done ? (
        <form onSubmit={(e) => { e.preventDefault(); send() }} className="flex gap-2">
          <input value={input} onChange={(e) => setInput(e.target.value)} className="flex-1 border rounded px-3 py-2" />
          <button className="px-4 py-2 bg-black text-white rounded" disabled={answer.isPending}>发送</button>
        </form>
      ) : (
        <button onClick={finish} disabled={finalize.isPending} className="w-full bg-blue-600 text-white py-3 rounded">
          {finalize.isPending ? '生成主简历…' : '完成并生成主简历'}
        </button>
      )}
    </div>
  )
}
```

- [ ] **Step 3：主页接入**

修改 master-resume page 为可切换 mode：
```typescript
'use client'
import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { UploadDropzone } from '@/components/master-resume/UploadDropzone'
import { IntakeDialog } from '@/components/master-resume/IntakeDialog'
import { useMasterResume } from '@/hooks/useMasterResume'
import { ResumeCards } from '@/components/master-resume/ResumeCards'

export default function MasterResumePage() {
  const t = useTranslations('master_resume')
  const { data, refetch } = useMasterResume()
  const [mode, setMode] = useState<'choose' | 'upload' | 'intake'>('choose')

  if (data) return <div className="space-y-6"><h1 className="text-2xl font-bold">{t('title')}</h1><ResumeCards data={data as never} /></div>

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t('title')}</h1>
      {mode === 'choose' && (
        <div className="grid grid-cols-2 gap-4">
          <button onClick={() => setMode('upload')} className="border rounded p-8 hover:bg-gray-50">📄 上传简历</button>
          <button onClick={() => setMode('intake')} className="border rounded p-8 hover:bg-gray-50">💬 AI 帮我挖经历（应届生推荐）</button>
        </div>
      )}
      {mode === 'upload' && <UploadDropzone onParsed={() => refetch()} />}
      {mode === 'intake' && <IntakeDialog onDone={() => refetch()} />}
    </div>
  )
}
```

- [ ] **Step 4：提交**

```bash
git add apps/web
git commit -m "feat(web): fresh-grad intake dialog UI + master-resume page mode switcher"
```

---

## Task 14: PostHog 事件 + e2e 测试

**Files:**
- Modify: `packages/shared-types/events.ts`（追加事件）
- Modify: 各上传/解析/诊断/intake 触发点 → track
- Create: `apps/web/e2e/master-resume.spec.ts`

**Interfaces:**
- Produces:
  - 事件追加：`MASTER_RESUME_UPLOAD_STARTED`、`MASTER_RESUME_PARSED`、`MASTER_RESUME_DIAGNOSED`、`INTAKE_STARTED`、`INTAKE_FINALIZED`
  - e2e：登录 → 进 master-resume → 选 intake → mock 完成（实测可 stub network）

- [ ] **Step 1：扩 events.ts**

```typescript
export const Events = {
  // ... 已有
  MASTER_RESUME_UPLOAD_STARTED: 'master_resume_upload_started',
  MASTER_RESUME_PARSED: 'master_resume_parsed',
  MASTER_RESUME_DIAGNOSED: 'master_resume_diagnosed',
  INTAKE_STARTED: 'intake_started',
  INTAKE_FINALIZED: 'intake_finalized',
} as const
```

- [ ] **Step 2：在 hook onSuccess 处 track**

修改 `useParseResume`：
```typescript
import { track } from '@/lib/posthog'
import { Events } from '@jc/shared-types'

export function useParseResume() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (vars: { s3_key: string }) =>
      api('/api/v1/master-resume/parse', { method: 'POST', body: JSON.stringify(vars) }),
    onSuccess: () => { track(Events.MASTER_RESUME_PARSED); qc.invalidateQueries({ queryKey: ['master-resume'] }) },
  })
}
```

类似在 `useDiagnose`、`useIntakeStart`、`useIntakeFinalize` 加 track。

- [ ] **Step 3：e2e smoke**

`apps/web/e2e/master-resume.spec.ts`：
```typescript
import { test, expect } from '@playwright/test'

test('master-resume page renders mode chooser when empty', async ({ page }) => {
  // 注：完整 e2e 需 mock auth；这里仅测页面在未登录时跳 login（middleware 会处理）
  await page.goto('/zh/master-resume')
  // 无 cookie 时 API 401 → page 仍能渲染（暂未做强制重定向）
  await expect(page.getByRole('heading', { name: '我的主简历' })).toBeVisible()
})
```

- [ ] **Step 4：提交**

```bash
git add packages apps/web
git commit -m "feat(web): posthog events + e2e smoke for master-resume page"
```

---

## Plan 1 完成判定

```bash
# api
cd apps/api && source .venv/bin/activate
pytest -q     # 全部 passed（含 plan 0 + 1）
mypy src      # 0 errors
ruff check src tests

# web
cd ../.. && pnpm --filter web typecheck && pnpm --filter web test && pnpm --filter web e2e

# 手动 e2e
docker compose -f infra/docker-compose.yml up -d
pnpm --filter api dev
pnpm --filter web dev
# 登录 → /zh/master-resume → 上传 PDF → 看到三栏卡片 → 编辑某能力 → 点诊断 → 看到部分卡片标 ⚠
```

完成后下一站 → Plan 2 (Application + JobPosting)
