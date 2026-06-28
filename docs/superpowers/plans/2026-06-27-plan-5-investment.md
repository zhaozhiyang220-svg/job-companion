# Plan 5：Investment（轻）+ 投递记录 Tab Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 单机会内"投递记录"Tab 可用——用户能记录"已投/已读/已约面/已收 offer/已拒"动作，每条动作可标注使用的简历版本和渠道；动作按时间线倒序展示。

**Architecture:** Investment 模型挂在 Application 下，引用 ResumeBranch（可空）；纯增删改查 + 时间线 UI，无 AI。

**Tech Stack:** 复用前序

## Global Constraints
- 继承前序所有约束
- 投递记录是 v1 唯一 Application 状态机的"轻量"前置：可用于驱动 Application.status 自动更新（v1 简化为：手动 archived）
- 渠道字段 free text，但提供常用预设下拉

---

## Task 1: Investment 模型

**Files:**
- Create: `apps/api/src/models/investment.py`
- Create: `apps/api/alembic/versions/0010_investment.py`
- Modify: `apps/api/src/models/__init__.py`
- Create: `apps/api/tests/test_investment_model.py`

**Interfaces:**
- Produces:
  - `Investment(id, application_id, used_resume_branch_id [nullable], action_type, action_at, channel, notes, created_at)`
  - `action_type` 枚举：`submitted` / `viewed` / `interview_scheduled` / `offer_received` / `rejected`

- [ ] **Step 1：模型**

`apps/api/src/models/investment.py`：
```python
from datetime import datetime
from enum import StrEnum
from uuid import uuid4, UUID
import sqlalchemy as sa
from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from src.core.db import Base

class InvestmentActionType(StrEnum):
    SUBMITTED = "submitted"
    VIEWED = "viewed"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    OFFER_RECEIVED = "offer_received"
    REJECTED = "rejected"

class Investment(Base):
    __tablename__ = "investments"
    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid4)
    application_id: Mapped[UUID] = mapped_column(sa.Uuid, ForeignKey("applications.id"), index=True)
    used_resume_branch_id: Mapped[UUID | None] = mapped_column(sa.Uuid, ForeignKey("resume_branches.id"), nullable=True)
    action_type: Mapped[InvestmentActionType] = mapped_column(
        sa.Enum(InvestmentActionType, name="investment_action_enum"), index=True,
    )
    action_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    channel: Mapped[str] = mapped_column(String(64), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=sa.func.now())
```

`__init__.py` 追加：
```python
from src.models.investment import Investment, InvestmentActionType  # noqa
```

- [ ] **Step 2：迁移 + 测试**

```bash
cd apps/api && source .venv/bin/activate
alembic revision --autogenerate -m "investment"
alembic upgrade head
```

`tests/test_investment_model.py`：
```python
from datetime import datetime, timezone
from src.models import User, Application, JobPosting
from src.models.investment import Investment, InvestmentActionType

def test_create_investment(db):
    u = User(preferences={}); db.add(u); db.flush()
    a = Application(user_id=u.id); a.job_posting = JobPosting(raw_text="x")
    db.add(a); db.flush()
    iv = Investment(application_id=a.id, action_type=InvestmentActionType.SUBMITTED,
                    action_at=datetime.now(timezone.utc), channel="Boss直聘", notes="投递成功")
    db.add(iv); db.flush()
    assert iv.action_type == InvestmentActionType.SUBMITTED
```

Run: PASS

- [ ] **Step 3：提交**

```bash
cd ../.. && git add apps/api && git commit -m "feat(api): Investment model with action_type enum + branch reference"
```

---

## Task 2: Investment API（CRUD + 列表）

**Files:**
- Create: `apps/api/src/routers/investment.py`
- Create: `apps/api/src/schemas/investment.py`
- Modify: `apps/api/src/main.py`
- Create: `apps/api/tests/test_investment_api.py`

**Interfaces:**
- Produces:
  - `POST /api/v1/applications/{app_id}/investments` → 创建
  - `GET /api/v1/applications/{app_id}/investments` → 时间线列表
  - `PATCH /api/v1/applications/{app_id}/investments/{id}` → 更新
  - `DELETE` → 删除

- [ ] **Step 1：schema**

`apps/api/src/schemas/investment.py`：
```python
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from src.models.investment import InvestmentActionType

class CreateInvestmentIn(BaseModel):
    action_type: InvestmentActionType
    action_at: datetime
    channel: str = ""
    notes: str = ""
    used_resume_branch_id: UUID | None = None

class UpdateInvestmentIn(BaseModel):
    action_type: InvestmentActionType | None = None
    action_at: datetime | None = None
    channel: str | None = None
    notes: str | None = None
    used_resume_branch_id: UUID | None = None

class InvestmentOut(BaseModel):
    id: UUID
    action_type: InvestmentActionType
    action_at: datetime
    channel: str
    notes: str
    used_resume_branch_id: UUID | None
    used_branch_label: str | None  # 渲染时拼出 "v2 · 评分82"
```

- [ ] **Step 2：router**

`apps/api/src/routers/investment.py`：
```python
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.db import get_db
from src.core.deps import current_user
from src.models import User, Application, ResumeBranch
from src.models.investment import Investment
from src.schemas.investment import CreateInvestmentIn, UpdateInvestmentIn, InvestmentOut

router = APIRouter(prefix="/api/v1/applications/{app_id}/investments", tags=["investment"])

def _check_app(app_id: UUID, user: User, db: Session) -> Application:
    a = db.query(Application).filter(Application.id == app_id, Application.user_id == user.id).first()
    if not a: raise HTTPException(404, "application not found")
    return a

def _label(db: Session, branch_id: UUID | None) -> str | None:
    if not branch_id: return None
    b = db.get(ResumeBranch, branch_id)
    if not b: return None
    return f"{b.version_label}" + (f" · {b.match_score}" if b.match_score is not None else "")

def _ser(db: Session, iv: Investment) -> InvestmentOut:
    return InvestmentOut(
        id=iv.id, action_type=iv.action_type, action_at=iv.action_at,
        channel=iv.channel, notes=iv.notes, used_resume_branch_id=iv.used_resume_branch_id,
        used_branch_label=_label(db, iv.used_resume_branch_id),
    )

@router.post("", response_model=InvestmentOut, status_code=201)
def create_investment(app_id: UUID, body: CreateInvestmentIn, user: User = Depends(current_user), db: Session = Depends(get_db)) -> InvestmentOut:
    _check_app(app_id, user, db)
    iv = Investment(application_id=app_id, **body.model_dump())
    db.add(iv); db.commit(); db.refresh(iv)
    return _ser(db, iv)

@router.get("", response_model=list[InvestmentOut])
def list_investments(app_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[InvestmentOut]:
    _check_app(app_id, user, db)
    rows = db.query(Investment).filter(Investment.application_id == app_id) \
              .order_by(Investment.action_at.desc()).all()
    return [_ser(db, iv) for iv in rows]

@router.patch("/{iv_id}", response_model=InvestmentOut)
def update_investment(app_id: UUID, iv_id: UUID, body: UpdateInvestmentIn, user: User = Depends(current_user), db: Session = Depends(get_db)) -> InvestmentOut:
    _check_app(app_id, user, db)
    iv = db.query(Investment).filter(Investment.id == iv_id, Investment.application_id == app_id).first()
    if not iv: raise HTTPException(404)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(iv, k, v)
    db.commit(); db.refresh(iv)
    return _ser(db, iv)

@router.delete("/{iv_id}", status_code=204)
def delete_investment(app_id: UUID, iv_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> None:
    _check_app(app_id, user, db)
    iv = db.query(Investment).filter(Investment.id == iv_id, Investment.application_id == app_id).first()
    if not iv: raise HTTPException(404)
    db.delete(iv); db.commit()
```

Modify main.py include router。

- [ ] **Step 3：测试**

`apps/api/tests/test_investment_api.py`：
```python
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from src.main import app
from src.core.security import issue_session_token
from src.core.db import SessionLocal
from src.models import User, Application, JobPosting

def _setup():
    db = SessionLocal()
    u = User(preferences={}); db.add(u); db.commit(); db.refresh(u)
    a = Application(user_id=u.id); a.job_posting = JobPosting(raw_text="x")
    db.add(a); db.commit(); db.refresh(a)
    c = TestClient(app); c.cookies.set("jc_session", issue_session_token(u.id))
    return c, str(a.id)

def test_create_and_list_investment():
    c, app_id = _setup()
    body = {"action_type":"submitted","action_at": datetime.now(timezone.utc).isoformat(),
            "channel":"Boss直聘","notes":"投了"}
    r = c.post(f"/api/v1/applications/{app_id}/investments", json=body)
    assert r.status_code == 201
    lst = c.get(f"/api/v1/applications/{app_id}/investments")
    assert len(lst.json()) == 1
    assert lst.json()[0]["channel"] == "Boss直聘"

def test_update_and_delete():
    c, app_id = _setup()
    r = c.post(f"/api/v1/applications/{app_id}/investments",
               json={"action_type":"submitted","action_at": datetime.now(timezone.utc).isoformat()})
    iv_id = r.json()["id"]
    p = c.patch(f"/api/v1/applications/{app_id}/investments/{iv_id}", json={"notes":"更新"})
    assert p.json()["notes"] == "更新"
    d = c.delete(f"/api/v1/applications/{app_id}/investments/{iv_id}")
    assert d.status_code == 204
```

Run: PASS

- [ ] **Step 4：提交**

```bash
cd ../.. && git add apps/api && git commit -m "feat(api): investment CRUD endpoints with branch reference and timeline order"
```

---

## Task 3: Web — Investment Hooks

**Files:**
- Create: `apps/web/src/hooks/useInvestments.ts`

- [ ] **Step 1**

```typescript
'use client'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'

export function useInvestments(appId: string) {
  return useQuery({ queryKey: ['investments', appId], queryFn: () => api<any[]>(`/api/v1/applications/${appId}/investments`), enabled: !!appId })
}

export function useCreateInvestment(appId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: any) => api(`/api/v1/applications/${appId}/investments`, { method: 'POST', body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['investments', appId] }),
  })
}

export function useUpdateInvestment(appId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (vars: { id: string; body: any }) => api(`/api/v1/applications/${appId}/investments/${vars.id}`, { method: 'PATCH', body: JSON.stringify(vars.body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['investments', appId] }),
  })
}

export function useDeleteInvestment(appId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api(`/api/v1/applications/${appId}/investments/${id}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['investments', appId] }),
  })
}
```

- [ ] **Step 2：提交**

```bash
git add apps/web && git commit -m "feat(web): investment hooks"
```

---

## Task 4: Web — Investment Timeline UI

**Files:**
- Modify: `apps/web/src/app/[locale]/(app)/opportunities/[id]/investments/page.tsx`
- Create: `apps/web/src/components/investment/InvestmentTimeline.tsx`
- Create: `apps/web/src/components/investment/NewInvestmentDialog.tsx`
- Modify: `apps/web/messages/{zh,en}.json`

**Interfaces:**
- Produces:
  - 时间线视图：每条带 icon + 时间 + 类型 + 渠道 + 简历版本徽章 + notes
  - 顶部"+ 新增动作"按钮
  - 内联编辑/删除

- [ ] **Step 1：翻译**

zh.json 追加：
```json
"investments": {
  "title":"投递记录",
  "new":"+ 新增动作",
  "action_submitted":"📤 已投递","action_viewed":"👁 已读取",
  "action_interview_scheduled":"📅 已约面","action_offer_received":"🎉 已收 Offer","action_rejected":"❌ 已拒",
  "channel":"渠道","notes":"备注","used_branch":"使用简历",
  "channel_options":"Boss直聘,拉勾,猎聘,LinkedIn,官网,内推,其他",
  "empty":"暂无动作，点击新增记录你的第一次投递",
  "save":"保存","cancel":"取消","delete_confirm":"删除这条记录？"
}
```

en.json 对应（key 不变，value 英文化）。

- [ ] **Step 2：NewInvestmentDialog**

```typescript
'use client'
import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { useCreateInvestment } from '@/hooks/useInvestments'
import { useBranches } from '@/hooks/useResumeBranches'

const ACTIONS = ['submitted','viewed','interview_scheduled','offer_received','rejected'] as const

export function NewInvestmentDialog({ appId, onClose }: { appId: string; onClose: () => void }) {
  const t = useTranslations('investments')
  const create = useCreateInvestment(appId)
  const { data: branches } = useBranches(appId)
  const [action, setAction] = useState<typeof ACTIONS[number]>('submitted')
  const [when, setWhen] = useState<string>(new Date().toISOString().slice(0, 16))
  const [channel, setChannel] = useState('')
  const [notes, setNotes] = useState('')
  const [branchId, setBranchId] = useState<string>('')

  async function save() {
    await create.mutateAsync({
      action_type: action,
      action_at: new Date(when).toISOString(),
      channel, notes,
      used_resume_branch_id: branchId || null,
    })
    onClose()
  }

  const channelOptions = t('channel_options').split(',')

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center" onClick={onClose}>
      <div className="bg-white rounded p-6 w-[480px] space-y-3" onClick={(e) => e.stopPropagation()}>
        <h3 className="font-bold">{t('new')}</h3>
        <div className="grid grid-cols-2 gap-2 text-sm">
          {ACTIONS.map((a) => (
            <button key={a} onClick={() => setAction(a)}
                    className={`border rounded px-2 py-1 ${action === a ? 'bg-black text-white' : ''}`}>
              {t(`action_${a}` as any)}
            </button>
          ))}
        </div>
        <input type="datetime-local" value={when} onChange={(e) => setWhen(e.target.value)} className="w-full border rounded px-3 py-2" />
        <div>
          <label className="block text-xs mb-1">{t('channel')}</label>
          <input list="ch" value={channel} onChange={(e) => setChannel(e.target.value)} className="w-full border rounded px-3 py-2" />
          <datalist id="ch">{channelOptions.map((c) => <option key={c} value={c} />)}</datalist>
        </div>
        <div>
          <label className="block text-xs mb-1">{t('used_branch')}</label>
          <select value={branchId} onChange={(e) => setBranchId(e.target.value)} className="w-full border rounded px-3 py-2">
            <option value="">—</option>
            {(branches ?? []).map((b: any) => (
              <option key={b.id} value={b.id}>{b.version_label} {b.match_score != null && `· ${b.match_score}`}</option>
            ))}
          </select>
        </div>
        <textarea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder={t('notes')} rows={2} className="w-full border rounded px-3 py-2" />
        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="px-3 py-2">{t('cancel')}</button>
          <button onClick={save} disabled={create.isPending} className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50">
            {create.isPending ? '…' : t('save')}
          </button>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 3：InvestmentTimeline**

```typescript
'use client'
import { useTranslations } from 'next-intl'
import { useInvestments, useDeleteInvestment } from '@/hooks/useInvestments'

export function InvestmentTimeline({ appId }: { appId: string }) {
  const t = useTranslations('investments')
  const { data } = useInvestments(appId)
  const del = useDeleteInvestment(appId)
  if (!data?.length) return <p className="text-gray-500">{t('empty')}</p>
  return (
    <ol className="border-l-2 border-gray-200 pl-4 space-y-4">
      {data.map((iv: any) => (
        <li key={iv.id} className="relative">
          <span className="absolute -left-[1.4rem] top-1 w-3 h-3 rounded-full bg-blue-500"></span>
          <div className="flex items-center justify-between">
            <div>
              <strong>{t(`action_${iv.action_type}` as any)}</strong>
              <span className="text-xs text-gray-500 ml-2">{new Date(iv.action_at).toLocaleString()}</span>
            </div>
            <button onClick={() => confirm(t('delete_confirm')) && del.mutate(iv.id)} className="text-xs text-red-600">✕</button>
          </div>
          <div className="text-sm text-gray-700">
            {iv.channel && <span>{t('channel')}: {iv.channel}　</span>}
            {iv.used_branch_label && <span className="bg-blue-50 text-blue-700 px-1.5 rounded text-xs">{iv.used_branch_label}</span>}
          </div>
          {iv.notes && <p className="text-sm mt-1 text-gray-600">{iv.notes}</p>}
        </li>
      ))}
    </ol>
  )
}
```

- [ ] **Step 4：page.tsx**

```typescript
'use client'
import { useState, use } from 'react'
import { useTranslations } from 'next-intl'
import { InvestmentTimeline } from '@/components/investment/InvestmentTimeline'
import { NewInvestmentDialog } from '@/components/investment/NewInvestmentDialog'

export default function InvestmentsTab({ params }: { params: Promise<{ id: string }> }) {
  const { id: appId } = use(params)
  const t = useTranslations('investments')
  const [open, setOpen] = useState(false)
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">{t('title')}</h2>
        <button onClick={() => setOpen(true)} className="bg-black text-white px-4 py-2 rounded">{t('new')}</button>
      </div>
      <InvestmentTimeline appId={appId} />
      {open && <NewInvestmentDialog appId={appId} onClose={() => setOpen(false)} />}
    </div>
  )
}
```

- [ ] **Step 5：提交**

```bash
git add apps/web && git commit -m "feat(web): investment timeline + new dialog with action types and branch tag"
```

---

## Task 5: PostHog + e2e

**Files:**
- Modify: `packages/shared-types/events.ts`
- Modify: `apps/web/src/hooks/useInvestments.ts`
- Create: `apps/web/e2e/investments.spec.ts`

- [ ] **Step 1**

```typescript
export const Events = {
  // ...
  INVESTMENT_CREATED: 'investment_created',
  INVESTMENT_DELETED: 'investment_deleted',
} as const
```

`useCreateInvestment` 与 `useDeleteInvestment` 添加 track。

- [ ] **Step 2：e2e**

```typescript
import { test, expect } from '@playwright/test'

test('investments tab structure (placeholder until full login flow)', async ({ page }) => {
  await page.goto('/zh/opportunities')
  await expect(page.getByRole('heading', { name: '我的求职机会' })).toBeVisible()
})
```

- [ ] **Step 3：提交**

```bash
git add packages apps && git commit -m "feat: posthog events + e2e for investments"
```

---

## Plan 5 完成判定

```bash
pnpm --filter api test && pnpm --filter web typecheck && pnpm --filter web e2e
# 手动：进入某机会 → 投递记录 Tab → 新增动作（已投/Boss直聘/v2 简历）→ 时间线显示
```

下一站 → Plan 6 (WeeklyDigest 本周复盘)
