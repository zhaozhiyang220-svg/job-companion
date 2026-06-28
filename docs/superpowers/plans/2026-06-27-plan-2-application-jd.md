# Plan 2：Application + JobPosting 模块 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 用户能新增求职机会（粘 JD 文本/链接）→ AI 解析 JD → 看到求职机会列表 → 进入单机会的 5 列 Tab 壳（仅 v1 必做的"简历定制"与"投递记录"在后续 plan 点亮，其余灰显）。

**Architecture:** Application 作为 v1 的数据中心实体（不以 Resume 为中心）；JobPosting 作为 Application 1:1 内嵌（数据上独立表，但 API 总是返回组合）；状态机 v1 仅 `drafting/archived`，预留 v2 字段；列表筛选 + 容量限制 + 资源多对多关联 stub。

**Tech Stack:** 复用 Plan 0+1 全部技术栈；JD 解析用 abab6.5s-chat（MiniMax 轻档，成本敏感）

## Global Constraints
- 继承 Plan 0/1 全部约束
- 容量上限：v1 用户最多 20 进行中、月新建 ≤ 15、超限走 `<CapacityGate />`（v1 此组件最小实现）
- Application 必须暴露 `linked_resources` 字段（多对多接口预留），实际 Resource 实体在 Plan 4 实现
- 5 列 Tab 灰显项 hover 显示"v2/v3 即将上线"路线图广告

---

## Task 1: Application + JobPosting 模型

**Files:**
- Create: `apps/api/src/models/application.py`
- Create: `apps/api/src/models/job_posting.py`
- Create: `apps/api/alembic/versions/0006_application_jobposting.py`
- Modify: `apps/api/src/models/__init__.py`
- Create: `apps/api/tests/test_application_models.py`

**Interfaces:**
- Produces:
  - `Application(id, user_id, status, priority, notes, created_at, last_active_at)`
  - `JobPosting(id, application_id [unique], raw_text, source_url, company_name, job_title, department, salary_range, location, language, requirements_parsed JSON, hidden_preferences JSON, red_flags JSON, parsed_at)`
  - `Application.status` 枚举：`drafting / archived`（v2 扩 applied/interviewing/offered/rejected）

- [ ] **Step 1：模型**

`apps/api/src/models/application.py`：
```python
from datetime import datetime
from uuid import uuid4, UUID
from enum import StrEnum
import sqlalchemy as sa
from sqlalchemy import String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.db import Base

class ApplicationStatus(StrEnum):
    DRAFTING = "drafting"
    ARCHIVED = "archived"
    # v2 extensions reserved
    APPLIED = "applied"
    INTERVIEWING = "interviewing"
    OFFERED = "offered"
    REJECTED = "rejected"

class Application(Base):
    __tablename__ = "applications"
    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(sa.Uuid, ForeignKey("users.id"), index=True)
    status: Mapped[ApplicationStatus] = mapped_column(
        sa.Enum(ApplicationStatus, name="application_status_enum"),
        default=ApplicationStatus.DRAFTING, index=True,
    )
    priority: Mapped[int] = mapped_column(Integer, default=3)  # 1-5
    notes: Mapped[str] = mapped_column(String(1024), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=sa.func.now())
    last_active_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())

    job_posting: Mapped["JobPosting"] = relationship(back_populates="application", uselist=False, cascade="all,delete-orphan")
```

`apps/api/src/models/job_posting.py`：
```python
from datetime import datetime
from uuid import uuid4, UUID
import sqlalchemy as sa
from sqlalchemy import String, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.db import Base

class JobPosting(Base):
    __tablename__ = "job_postings"
    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid4)
    application_id: Mapped[UUID] = mapped_column(sa.Uuid, ForeignKey("applications.id"), unique=True, index=True)
    raw_text: Mapped[str] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    company_name: Mapped[str] = mapped_column(String(256), default="")
    job_title: Mapped[str] = mapped_column(String(256), default="")
    department: Mapped[str] = mapped_column(String(128), default="")
    salary_range: Mapped[str] = mapped_column(String(64), default="")
    location: Mapped[str] = mapped_column(String(128), default="")
    language: Mapped[str] = mapped_column(String(8), default="zh")
    requirements_parsed: Mapped[dict] = mapped_column(JSON, default=dict)
    hidden_preferences: Mapped[list] = mapped_column(JSON, default=list)
    red_flags: Mapped[list] = mapped_column(JSON, default=list)
    parsed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    application: Mapped["Application"] = relationship(back_populates="job_posting")
```

`apps/api/src/models/__init__.py` 追加：
```python
from src.models.application import Application, ApplicationStatus  # noqa: F401
from src.models.job_posting import JobPosting  # noqa: F401
```

- [ ] **Step 2：迁移**

```bash
cd apps/api && source .venv/bin/activate
alembic revision --autogenerate -m "application and job_posting"
alembic upgrade head
```

- [ ] **Step 3：测试**

`apps/api/tests/test_application_models.py`：
```python
from src.models import User, Application, ApplicationStatus, JobPosting

def test_application_with_job_posting(db):
    u = User(preferences={}); db.add(u); db.flush()
    app = Application(user_id=u.id, status=ApplicationStatus.DRAFTING, notes="字节豆包")
    app.job_posting = JobPosting(raw_text="JD text...", company_name="字节", job_title="PM")
    db.add(app); db.flush()
    assert app.job_posting.company_name == "字节"
    assert app.status == ApplicationStatus.DRAFTING
```

Run: `pytest -q tests/test_application_models.py` → PASS

- [ ] **Step 4：提交**

```bash
cd ../.. && git add apps/api
git commit -m "feat(api): Application + JobPosting models with reserved v2 status fields"
```

---

## Task 2: AI JD 解析 Prompt + Service

**Files:**
- Create: `apps/api/src/ai/prompts/parse_jd.py`
- Create: `apps/api/src/services/jd_parser.py`
- Create: `apps/api/src/schemas/jd.py`
- Create: `apps/api/tests/test_jd_parser.py`

**Interfaces:**
- Produces:
  - `ParsedJD` schema：company_name / job_title / department / salary_range / location / language / requirements{hard:[], soft:[], years:str} / hidden_preferences:[] / red_flags:[]
  - `async parse_jd(text: str, user_id: UUID) -> ParsedJD`

- [ ] **Step 1：prompt**

```python
PARSE_JD_SYSTEM = """你是 JD 拆解专家。输入一段招聘 JD 原文，输出严格 JSON：
{
  "company_name": str, "job_title": str, "department": str,
  "salary_range": str, "location": str, "language": "zh"|"en",
  "requirements": {
      "hard": [str], "soft": [str], "years": str
  },
  "hidden_preferences": [str],   // 你能从字里行间读出的偏好（如"抗压""能加班"）
  "red_flags": [str]             // 雷区（如"全员持股""扁平管理"潜台词）
}
- 抽不到字段填空字符串/空数组
- 语言判断：JD 主体含中文以上 50% 字符判 zh，否则 en
- 仅 JSON，无 markdown
"""
```

- [ ] **Step 2：schema**

`apps/api/src/schemas/jd.py`：
```python
from pydantic import BaseModel

class JDRequirements(BaseModel):
    hard: list[str] = []
    soft: list[str] = []
    years: str = ""

class ParsedJD(BaseModel):
    company_name: str = ""
    job_title: str = ""
    department: str = ""
    salary_range: str = ""
    location: str = ""
    language: str = "zh"
    requirements: JDRequirements = JDRequirements()
    hidden_preferences: list[str] = []
    red_flags: list[str] = []
```

- [ ] **Step 3：service**

`apps/api/src/services/jd_parser.py`：
```python
from uuid import UUID
from src.ai.llm_client import LLMClient
from src.ai.prompts.parse_jd import PARSE_JD_SYSTEM
from src.schemas.jd import ParsedJD

_llm = LLMClient()

async def parse_jd(text: str, user_id: UUID) -> ParsedJD:
    raw = await _llm.acomplete(
        model="auto-light",
        system=PARSE_JD_SYSTEM,
        messages=[{"role":"user","content": text}],
        max_tokens=1024, user_id=user_id, scene="jd_parse",
    )
    return ParsedJD.model_validate_json(raw)
```

- [ ] **Step 4：测试**

```python
import json
from unittest.mock import patch, AsyncMock
from uuid import uuid4
import pytest
from src.services.jd_parser import parse_jd

@pytest.mark.asyncio
async def test_parse_jd():
    fake = {"company_name":"字节","job_title":"PM","department":"豆包","salary_range":"24-40k",
            "location":"北京","language":"zh",
            "requirements":{"hard":["PM 经验"],"soft":["主动"],"years":"3-5"},
            "hidden_preferences":["抗压"], "red_flags":[]}
    with patch("src.services.jd_parser._llm.acomplete", AsyncMock(return_value=json.dumps(fake))):
        out = await parse_jd("...", uuid4())
    assert out.company_name == "字节"
    assert out.requirements.hard == ["PM 经验"]
```

Run: `pytest -q tests/test_jd_parser.py` → PASS

- [ ] **Step 5：提交**

```bash
git add apps/api && git commit -m "feat(api): AI JD parser (abab6.5s-chat) -> ParsedJD schema"
```

---

## Task 3: Application API — Create / List / Get

**Files:**
- Create: `apps/api/src/routers/application.py`
- Create: `apps/api/src/schemas/application.py`
- Modify: `apps/api/src/main.py`
- Create: `apps/api/tests/test_application_api.py`

**Interfaces:**
- Produces:
  - `POST /api/v1/applications` body `{raw_text: str, source_url?: str}` → 解析 JD + 落库 → 返回 Application
  - `GET /api/v1/applications` 查询参 `status=drafting|archived&page=1&page_size=20` → 列表
  - `GET /api/v1/applications/{id}` → 单条详情（含 job_posting）
  - `PATCH /api/v1/applications/{id}` body `{status?, priority?, notes?}` → 更新

- [ ] **Step 1：schema**

```python
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from src.models.application import ApplicationStatus
from src.schemas.jd import JDRequirements

class CreateApplicationIn(BaseModel):
    raw_text: str
    source_url: str | None = None

class UpdateApplicationIn(BaseModel):
    status: ApplicationStatus | None = None
    priority: int | None = None
    notes: str | None = None

class JobPostingOut(BaseModel):
    company_name: str; job_title: str; department: str
    salary_range: str; location: str; language: str
    requirements_parsed: dict; hidden_preferences: list[str]; red_flags: list[str]
    raw_text: str; source_url: str | None

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
```

- [ ] **Step 2：router**

`apps/api/src/routers/application.py`：
```python
from datetime import datetime, timezone, timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func
from src.core.db import get_db
from src.core.deps import current_user
from src.models import User, Application, ApplicationStatus, JobPosting
from src.services.jd_parser import parse_jd
from src.schemas.application import (
    CreateApplicationIn, UpdateApplicationIn, ApplicationOut, ApplicationListItem,
    ApplicationList, JobPostingOut,
)

router = APIRouter(prefix="/api/v1/applications", tags=["applications"])

MAX_ACTIVE = 20
MAX_PER_MONTH = 15

def _serialize(a: Application) -> ApplicationOut:
    jp = a.job_posting
    return ApplicationOut(
        id=a.id, status=a.status, priority=a.priority, notes=a.notes,
        created_at=a.created_at, last_active_at=a.last_active_at,
        job_posting=JobPostingOut(
            company_name=jp.company_name, job_title=jp.job_title, department=jp.department,
            salary_range=jp.salary_range, location=jp.location, language=jp.language,
            requirements_parsed=jp.requirements_parsed, hidden_preferences=jp.hidden_preferences,
            red_flags=jp.red_flags, raw_text=jp.raw_text, source_url=jp.source_url,
        ),
    )

def _check_capacity(db: Session, user: User) -> None:
    active = db.query(func.count(Application.id)).filter(
        Application.user_id == user.id, Application.status != ApplicationStatus.ARCHIVED,
    ).scalar() or 0
    if active >= MAX_ACTIVE:
        raise HTTPException(409, {"code": "capacity_active", "message": f"已达上限 {MAX_ACTIVE}，请归档旧机会"})
    since = datetime.now(timezone.utc) - timedelta(days=30)
    monthly = db.query(func.count(Application.id)).filter(
        Application.user_id == user.id, Application.created_at >= since,
    ).scalar() or 0
    if monthly >= MAX_PER_MONTH:
        raise HTTPException(409, {"code": "capacity_monthly", "message": f"30 天内新建已达 {MAX_PER_MONTH}，建议找 Coach 帮你聚焦"})

@router.post("", response_model=ApplicationOut, status_code=201)
async def create_application(body: CreateApplicationIn, user: User = Depends(current_user), db: Session = Depends(get_db)) -> ApplicationOut:
    _check_capacity(db, user)
    parsed = await parse_jd(body.raw_text, user.id)
    app = Application(user_id=user.id)
    app.job_posting = JobPosting(
        raw_text=body.raw_text, source_url=body.source_url,
        company_name=parsed.company_name, job_title=parsed.job_title,
        department=parsed.department, salary_range=parsed.salary_range,
        location=parsed.location, language=parsed.language,
        requirements_parsed=parsed.requirements.model_dump(),
        hidden_preferences=parsed.hidden_preferences, red_flags=parsed.red_flags,
        parsed_at=datetime.now(timezone.utc),
    )
    db.add(app); db.commit(); db.refresh(app)
    return _serialize(app)

@router.get("", response_model=ApplicationList)
def list_applications(
    status: ApplicationStatus | None = None,
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(current_user), db: Session = Depends(get_db),
) -> ApplicationList:
    q = db.query(Application).filter(Application.user_id == user.id)
    if status: q = q.filter(Application.status == status)
    total = q.count()
    rows = q.options(selectinload(Application.job_posting)).order_by(Application.last_active_at.desc()) \
        .offset((page-1)*page_size).limit(page_size).all()
    items = [ApplicationListItem(
        id=a.id, status=a.status,
        company_name=a.job_posting.company_name, job_title=a.job_posting.job_title,
        department=a.job_posting.department, salary_range=a.job_posting.salary_range,
        last_active_at=a.last_active_at,
    ) for a in rows]
    return ApplicationList(items=items, total=total, page=page, page_size=page_size)

@router.get("/{app_id}", response_model=ApplicationOut)
def get_application(app_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> ApplicationOut:
    a = db.query(Application).filter(Application.id == app_id, Application.user_id == user.id) \
         .options(selectinload(Application.job_posting)).first()
    if not a: raise HTTPException(404, "not found")
    return _serialize(a)

@router.patch("/{app_id}", response_model=ApplicationOut)
def update_application(app_id: UUID, body: UpdateApplicationIn, user: User = Depends(current_user), db: Session = Depends(get_db)) -> ApplicationOut:
    a = db.query(Application).filter(Application.id == app_id, Application.user_id == user.id).first()
    if not a: raise HTTPException(404, "not found")
    if body.status is not None: a.status = body.status
    if body.priority is not None: a.priority = body.priority
    if body.notes is not None: a.notes = body.notes
    db.commit(); db.refresh(a)
    return _serialize(a)
```

Modify `main.py` 加入 application router include。

- [ ] **Step 3：测试**

`apps/api/tests/test_application_api.py`：
```python
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from src.main import app
from src.core.security import issue_session_token
from src.core.db import SessionLocal
from src.models import User
from src.schemas.jd import ParsedJD, JDRequirements

def _login():
    db = SessionLocal()
    u = User(preferences={}); db.add(u); db.commit(); db.refresh(u)
    c = TestClient(app); c.cookies.set("jc_session", issue_session_token(u.id))
    return c

def test_create_and_list_application():
    fake = ParsedJD(company_name="字节", job_title="PM", requirements=JDRequirements(hard=["PM"]))
    with patch("src.routers.application.parse_jd", AsyncMock(return_value=fake)):
        c = _login()
        r1 = c.post("/api/v1/applications", json={"raw_text":"...PM..."})
        assert r1.status_code == 201
        assert r1.json()["job_posting"]["company_name"] == "字节"

        r2 = c.get("/api/v1/applications")
        assert r2.json()["total"] == 1

def test_capacity_limit_active():
    fake = ParsedJD()
    with patch("src.routers.application.parse_jd", AsyncMock(return_value=fake)):
        c = _login()
        for _ in range(20):
            c.post("/api/v1/applications", json={"raw_text":"x"})
        r = c.post("/api/v1/applications", json={"raw_text":"x"})
        assert r.status_code == 409
        assert r.json()["detail"]["code"] == "capacity_active"
```

Run: `pytest -q tests/test_application_api.py` → PASS

- [ ] **Step 4：提交**

```bash
cd ../.. && git add apps/api && git commit -m "feat(api): application CRUD + JD auto-parse + capacity limits"
```

---

## Task 4: Web — Opportunities List Page

**Files:**
- Create: `apps/web/src/hooks/useApplications.ts`
- Modify: `apps/web/src/app/[locale]/(app)/opportunities/page.tsx`
- Create: `apps/web/src/components/opportunities/OpportunityCard.tsx`
- Create: `apps/web/src/components/opportunities/NewOpportunityDialog.tsx`
- Modify: `apps/web/messages/{zh,en}.json`（追加 opportunities 文案）

**Interfaces:**
- Produces:
  - `useApplications(status?)`、`useApplication(id)`、`useCreateApplication()`、`useUpdateApplication()`
  - 列表页：3 个 tab 筛（全部 / 进行中 / 已归档）+ 卡片列表 + "+ 新增机会"按钮
  - 新建机会 Dialog：粘贴 JD → 提交

- [ ] **Step 1：hooks**

```typescript
'use client'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'

export type ApplicationStatus = 'drafting' | 'archived'

export function useApplications(status?: ApplicationStatus) {
  return useQuery({
    queryKey: ['applications', status],
    queryFn: () => api<{ items: any[]; total: number }>(`/api/v1/applications${status ? `?status=${status}` : ''}`),
  })
}

export function useApplication(id: string) {
  return useQuery({
    queryKey: ['application', id],
    queryFn: () => api<any>(`/api/v1/applications/${id}`),
    enabled: Boolean(id),
  })
}

export function useCreateApplication() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { raw_text: string; source_url?: string }) =>
      api('/api/v1/applications', { method: 'POST', body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['applications'] }),
  })
}

export function useUpdateApplication(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { status?: string; priority?: number; notes?: string }) =>
      api(`/api/v1/applications/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['applications'] }); qc.invalidateQueries({ queryKey: ['application', id] }) },
  })
}
```

- [ ] **Step 2：翻译**

`zh.json` 追加：
```json
"opportunities": {
  "title": "我的求职机会",
  "tab_all": "全部", "tab_drafting": "进行中", "tab_archived": "已归档",
  "new": "+ 新增机会", "paste_jd": "粘贴 JD 文本",
  "submit": "解析并创建", "parsing": "AI 解析中…",
  "no_company": "未知公司", "empty": "还没有机会，先粘贴一个 JD 试试",
  "capacity_active_exceeded": "已达进行中机会上限，请归档旧的"
}
```

`en.json` 对应翻译。

- [ ] **Step 3：OpportunityCard**

```typescript
'use client'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useTranslations } from 'next-intl'

export function OpportunityCard({ item }: { item: any }) {
  const t = useTranslations('opportunities')
  const { locale } = useParams<{ locale: string }>()
  return (
    <Link href={`/${locale}/opportunities/${item.id}`}
          className="block border rounded p-4 hover:bg-gray-50">
      <div className="flex items-center justify-between">
        <strong>{item.company_name || t('no_company')} · {item.job_title}</strong>
        <span className="text-xs text-gray-500">{item.status}</span>
      </div>
      <div className="text-sm text-gray-600">{item.department} · {item.salary_range}</div>
      <div className="text-xs text-gray-400">最近更新 {new Date(item.last_active_at).toLocaleDateString()}</div>
    </Link>
  )
}
```

- [ ] **Step 4：NewOpportunityDialog**

```typescript
'use client'
import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { useCreateApplication } from '@/hooks/useApplications'

export function NewOpportunityDialog({ onClose }: { onClose: () => void }) {
  const t = useTranslations('opportunities')
  const [text, setText] = useState('')
  const [err, setErr] = useState<string | null>(null)
  const create = useCreateApplication()
  async function submit() {
    setErr(null)
    try {
      await create.mutateAsync({ raw_text: text })
      onClose()
    } catch (e: any) {
      if (String(e).includes('409')) setErr(t('capacity_active_exceeded'))
      else setErr(String(e))
    }
  }
  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center" onClick={onClose}>
      <div className="bg-white rounded p-6 w-[640px] max-w-[95%]" onClick={(e) => e.stopPropagation()}>
        <h3 className="font-bold mb-3">{t('new')}</h3>
        <textarea value={text} onChange={(e) => setText(e.target.value)} rows={10}
                  placeholder={t('paste_jd')} className="w-full border rounded p-2" />
        {err && <p className="text-red-700 text-sm mt-2">{err}</p>}
        <div className="flex justify-end gap-2 mt-3">
          <button onClick={onClose} className="px-3 py-2">取消</button>
          <button onClick={submit} disabled={create.isPending || !text.trim()}
                  className="px-4 py-2 bg-black text-white rounded disabled:opacity-50">
            {create.isPending ? t('parsing') : t('submit')}
          </button>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 5：opportunities/page.tsx**

```typescript
'use client'
import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { useApplications, type ApplicationStatus } from '@/hooks/useApplications'
import { OpportunityCard } from '@/components/opportunities/OpportunityCard'
import { NewOpportunityDialog } from '@/components/opportunities/NewOpportunityDialog'

export default function OpportunitiesPage() {
  const t = useTranslations('opportunities')
  const [tab, setTab] = useState<ApplicationStatus | undefined>(undefined)
  const [open, setOpen] = useState(false)
  const { data } = useApplications(tab)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{t('title')}</h1>
        <button onClick={() => setOpen(true)} className="bg-black text-white px-4 py-2 rounded">{t('new')}</button>
      </div>
      <div className="flex gap-3">
        {[
          { v: undefined, label: t('tab_all') },
          { v: 'drafting' as const, label: t('tab_drafting') },
          { v: 'archived' as const, label: t('tab_archived') },
        ].map((x) => (
          <button key={x.label} onClick={() => setTab(x.v)}
                  className={`px-3 py-1 rounded ${tab === x.v ? 'bg-black text-white' : 'border'}`}>{x.label}</button>
        ))}
      </div>
      <div className="space-y-3">
        {(data?.items ?? []).map((it: any) => <OpportunityCard key={it.id} item={it} />)}
        {data?.items?.length === 0 && <p className="text-gray-500">{t('empty')}</p>}
      </div>
      {open && <NewOpportunityDialog onClose={() => setOpen(false)} />}
    </div>
  )
}
```

- [ ] **Step 6：提交**

```bash
git add apps/web && git commit -m "feat(web): opportunities list page + new opportunity dialog"
```

---

## Task 5: Web — 单机会 5 列 Tab 壳

**Files:**
- Create: `apps/web/src/app/[locale]/(app)/opportunities/[id]/layout.tsx`
- Create: `apps/web/src/app/[locale]/(app)/opportunities/[id]/page.tsx`（redirect to /resume）
- Create: `apps/web/src/app/[locale]/(app)/opportunities/[id]/resume/page.tsx`（占位）
- Create: `apps/web/src/app/[locale]/(app)/opportunities/[id]/investments/page.tsx`（占位）
- Create: `apps/web/src/components/opportunities/OpportunityTabs.tsx`

**Interfaces:**
- Produces:
  - 进入 `/opportunities/{id}` → 默认跳 `/opportunities/{id}/resume`
  - Tabs：[简历定制 ✓] [投递记录 ✓] [面试准备 🔒v2] [面试复盘 🔒v3] [Offer 评估 🔒v3]
  - 灰显项 hover 弹气泡说明
  - 顶部展示公司/岗位/部门/薪资/JD 解析摘要

- [ ] **Step 1：OpportunityTabs**

```typescript
'use client'
import Link from 'next/link'
import { useParams, usePathname } from 'next/navigation'

const TABS = [
  { key: 'resume',      label: '📝 简历定制', enabled: true,  tooltip: '' },
  { key: 'investments', label: '📮 投递记录', enabled: true,  tooltip: '' },
  { key: 'interview',   label: '🎤 面试准备', enabled: false, tooltip: 'v2 上线 · JD 拆解 + 模拟面试' },
  { key: 'recap',       label: '📋 面试复盘', enabled: false, tooltip: 'v3 上线 · 录音转写 + AI 反馈' },
  { key: 'offer',       label: '💼 Offer 评估', enabled: false, tooltip: 'v3 上线 · 多 offer 对比 + 谈薪' },
]

export function OpportunityTabs({ appId }: { appId: string }) {
  const { locale } = useParams<{ locale: string }>()
  const path = usePathname()
  return (
    <nav className="flex gap-2 border-b">
      {TABS.map((t) => {
        const href = `/${locale}/opportunities/${appId}/${t.key}`
        const active = path === href
        if (!t.enabled) {
          return (
            <span key={t.key} title={t.tooltip}
                  className="px-3 py-2 text-gray-400 cursor-not-allowed">
              {t.label} 🔒
            </span>
          )
        }
        return (
          <Link key={t.key} href={href}
                className={`px-3 py-2 ${active ? 'border-b-2 border-black font-bold' : 'text-gray-700'}`}>
            {t.label}
          </Link>
        )
      })}
    </nav>
  )
}
```

- [ ] **Step 2：layout**

`apps/web/src/app/[locale]/(app)/opportunities/[id]/layout.tsx`：
```typescript
'use client'
import { use } from 'react'
import type { ReactNode } from 'react'
import { useApplication } from '@/hooks/useApplications'
import { OpportunityTabs } from '@/components/opportunities/OpportunityTabs'

export default function OppLayout({ children, params }: { children: ReactNode; params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const { data } = useApplication(id)
  return (
    <div className="space-y-4">
      <header className="border-b pb-3">
        <h1 className="text-xl font-bold">
          {data?.job_posting?.company_name || '加载中'} · {data?.job_posting?.job_title}
        </h1>
        <div className="text-sm text-gray-500">{data?.job_posting?.department} · {data?.job_posting?.salary_range}</div>
      </header>
      <OpportunityTabs appId={id} />
      <main>{children}</main>
    </div>
  )
}
```

- [ ] **Step 3：page.tsx 重定向 + 子页占位**

```typescript
// apps/web/src/app/[locale]/(app)/opportunities/[id]/page.tsx
import { redirect } from 'next/navigation'
export default async function Page({ params }: { params: Promise<{ locale: string; id: string }> }) {
  const { locale, id } = await params
  redirect(`/${locale}/opportunities/${id}/resume`)
}
```

```typescript
// resume/page.tsx
export default function ResumeTab() {
  return <p>简历定制模块 — 详见 Plan 3</p>
}
```

```typescript
// investments/page.tsx
export default function InvestmentsTab() {
  return <p>投递记录 — 详见 Plan 5</p>
}
```

- [ ] **Step 4：提交**

```bash
git add apps/web && git commit -m "feat(web): opportunity detail layout with 5-tab shell (2 lit, 3 disabled)"
```

---

## Task 6: 资源关联预留 + CapacityGate 组件

**Files:**
- Create: `apps/api/src/models/application_resource_link.py`（多对多关联表）
- Modify: `apps/api/src/models/application.py`（追加 relationship 占位）
- Create: `apps/api/alembic/versions/0007_application_resource_link.py`
- Create: `apps/web/src/components/common/CapacityGate.tsx`

**Interfaces:**
- Produces:
  - `application_resource_links` 表：application_id + resource_item_id（Resource 模型在 Plan 4 创建，但表此处先建）
  - `<CapacityGate code, onClose>`：根据 server 返回的 capacity_active/capacity_monthly 代码显示对应 Coach 导流弹窗

- [ ] **Step 1：关联表（reserve）**

`apps/api/src/models/application_resource_link.py`：
```python
from uuid import UUID
import sqlalchemy as sa
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from src.core.db import Base

class ApplicationResourceLink(Base):
    __tablename__ = "application_resource_links"
    application_id: Mapped[UUID] = mapped_column(sa.Uuid, ForeignKey("applications.id"), primary_key=True)
    resource_item_id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True)  # FK to resources, added in Plan 4
```

> 注：FK `resource_item_id → resource_items.id` 在 Plan 4 创建 ResourceItem 后用迁移补 FK 约束；v1 这里先逻辑性记录。

`apps/api/src/models/__init__.py` 追加：
```python
from src.models.application_resource_link import ApplicationResourceLink  # noqa: F401
```

- [ ] **Step 2：迁移**

```bash
cd apps/api && source .venv/bin/activate
alembic revision --autogenerate -m "application resource link table (FK to be added in plan 4)"
alembic upgrade head
```

- [ ] **Step 3：写 CapacityGate**

`apps/web/src/components/common/CapacityGate.tsx`：
```typescript
'use client'
import Link from 'next/link'
import { useParams } from 'next/navigation'

const MSG: Record<string, string> = {
  capacity_active: '你已经有 20 个进行中机会了，先归档一些再继续。',
  capacity_monthly: '30 天内新建机会数已达上限。要不要找 Coach 帮你聚焦？',
}

export function CapacityGate({ code, onClose }: { code: string; onClose: () => void }) {
  const { locale } = useParams<{ locale: string }>()
  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center" onClick={onClose}>
      <div className="bg-white rounded p-6 w-96" onClick={(e) => e.stopPropagation()}>
        <h3 className="font-bold">温馨提示</h3>
        <p className="mt-2 text-sm">{MSG[code] ?? '已达使用上限'}</p>
        <div className="mt-4 flex justify-end gap-2">
          <button onClick={onClose} className="px-3 py-2">关闭</button>
          <Link href={`/${locale}/coach`} onClick={onClose}
                className="px-4 py-2 bg-blue-600 text-white rounded">找 Coach</Link>
        </div>
      </div>
    </div>
  )
}
```

修改 NewOpportunityDialog 在 capacity_active 错误时用 CapacityGate 替代普通错误：
```typescript
import { CapacityGate } from '@/components/common/CapacityGate'
// ...
const [gateCode, setGateCode] = useState<string | null>(null)
async function submit() {
  try { await create.mutateAsync(...) }
  catch (e: any) {
    const m = String(e).match(/capacity_(active|monthly)/)
    if (m) { setGateCode(`capacity_${m[1]}`); return }
    setErr(String(e))
  }
}
// 在 return 末尾：{gateCode && <CapacityGate code={gateCode} onClose={() => setGateCode(null)} />}
```

- [ ] **Step 4：提交**

```bash
cd ../.. && git add apps/api apps/web
git commit -m "feat: application-resource link table reserved + CapacityGate component"
```

---

## Task 7: PostHog 事件 + e2e

**Files:**
- Modify: `packages/shared-types/events.ts`
- Modify: `apps/web/src/hooks/useApplications.ts`（onSuccess track）
- Create: `apps/web/e2e/opportunities.spec.ts`

**Interfaces:**
- Produces:
  - 事件：`OPPORTUNITY_CREATED`、`OPPORTUNITY_OPENED`、`OPPORTUNITY_ARCHIVED`
  - e2e：列表页可达、新增 dialog 可打开

- [ ] **Step 1：events**

```typescript
export const Events = {
  // ...
  OPPORTUNITY_CREATED: 'opportunity_created',
  OPPORTUNITY_OPENED: 'opportunity_opened',
  OPPORTUNITY_ARCHIVED: 'opportunity_archived',
} as const
```

- [ ] **Step 2：track**

```typescript
// useCreateApplication
import { track } from '@/lib/posthog'
import { Events } from '@jc/shared-types'

export function useCreateApplication() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (...) => ...,
    onSuccess: (data: any) => { track(Events.OPPORTUNITY_CREATED, { id: data.id }); qc.invalidateQueries({ queryKey: ['applications'] }) },
  })
}
```

OpportunityCard onClick 加 `track(Events.OPPORTUNITY_OPENED, { id: item.id })`。

- [ ] **Step 3：e2e**

`apps/web/e2e/opportunities.spec.ts`：
```typescript
import { test, expect } from '@playwright/test'

test('opportunities page loads', async ({ page }) => {
  await page.goto('/zh/opportunities')
  await expect(page.getByRole('heading', { name: '我的求职机会' })).toBeVisible()
  await expect(page.getByRole('button', { name: '+ 新增机会' })).toBeVisible()
})

test('new opportunity dialog opens', async ({ page }) => {
  await page.goto('/zh/opportunities')
  await page.getByRole('button', { name: '+ 新增机会' }).click()
  await expect(page.getByPlaceholder('粘贴 JD 文本')).toBeVisible()
})
```

- [ ] **Step 4：提交**

```bash
git add packages apps/web && git commit -m "feat: posthog events + e2e for opportunities"
```

---

## Plan 2 完成判定

```bash
pnpm --filter api test && pnpm --filter web typecheck && pnpm --filter web e2e
# 手动：登录 → /zh/opportunities → 新增（贴 JD）→ 看到列表 + 公司岗位 → 点击进入 → 看到 5 列 tab 壳
```

下一站 → Plan 3 (ResumeBranch + PatchOperations，最大的 plan)
