# Plan 7：Coach 导流 + 成本仪表盘 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:**
1. 用户能从机会页/简历页/容量超限弹窗提交 Coach 咨询表单 → PM 立即收 webhook 推送（飞书/邮件/Telegram 任选）；每周固定 5 slot，售罄 UI 自动锁
2. PM 自己用的内部成本仪表盘：DAU / MAU / AI 调用量 / 单用户成本 / 总开销（基础密码保护）

**Architecture:** CoachInquiry 表 + webhook 通知 + 容量计数；内部 dashboard 走独立路由前缀 `/internal/`，简单 password 中间件；数据从 `ai_call_logs` 和 `users` 聚合。

**Tech Stack:** 复用前序

## Global Constraints
- 继承前序所有约束
- 内部 dashboard 路径走 password 中间件，密码从 env 注入
- Coach slot 计数按本周（周一-周日 BJT）

---

## Task 1: CoachInquiry 模型

**Files:**
- Create: `apps/api/src/models/coach_inquiry.py`
- Create: `apps/api/alembic/versions/0012_coach_inquiry.py`
- Modify: `apps/api/src/models/__init__.py`
- Create: `apps/api/tests/test_coach_inquiry_model.py`

**Interfaces:**
- Produces:
  - `CoachInquiry(id, user_id, application_id [nullable], source_screen, contact_method, status, notes, created_at)`
  - `status` 枚举：`new / contacted / scheduled / converted / dropped`

- [ ] **Step 1：模型**

`apps/api/src/models/coach_inquiry.py`：
```python
from datetime import datetime
from enum import StrEnum
from uuid import uuid4, UUID
import sqlalchemy as sa
from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from src.core.db import Base

class CoachInquiryStatus(StrEnum):
    NEW = "new"
    CONTACTED = "contacted"
    SCHEDULED = "scheduled"
    CONVERTED = "converted"
    DROPPED = "dropped"

class CoachInquiry(Base):
    __tablename__ = "coach_inquiries"
    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(sa.Uuid, index=True)
    application_id: Mapped[UUID | None] = mapped_column(sa.Uuid, nullable=True)
    source_screen: Mapped[str] = mapped_column(String(64))  # e.g. resume_workspace / capacity_gate / weekly_action
    contact_method: Mapped[str] = mapped_column(String(128))  # 微信号/手机/email
    status: Mapped[CoachInquiryStatus] = mapped_column(sa.Enum(CoachInquiryStatus, name="coach_inquiry_status_enum"), default=CoachInquiryStatus.NEW)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=sa.func.now(), index=True)
```

`__init__.py` 追加：`from src.models.coach_inquiry import CoachInquiry, CoachInquiryStatus  # noqa`

- [ ] **Step 2：迁移**

```bash
cd apps/api && source .venv/bin/activate
alembic revision --autogenerate -m "coach inquiry"
alembic upgrade head
```

- [ ] **Step 3：测试**

```python
from src.models import User
from src.models.coach_inquiry import CoachInquiry, CoachInquiryStatus

def test_create_inquiry(db):
    u = User(preferences={}); db.add(u); db.flush()
    ci = CoachInquiry(user_id=u.id, source_screen="resume_workspace", contact_method="wx:zhangsan")
    db.add(ci); db.flush()
    assert ci.status == CoachInquiryStatus.NEW
```

Run: PASS

- [ ] **Step 4：提交**

```bash
cd ../.. && git add apps/api && git commit -m "feat(api): CoachInquiry model + status enum"
```

---

## Task 2: Notifier Service（飞书/邮件/Telegram 三选一）

**Files:**
- Create: `apps/api/src/services/notifier.py`
- Modify: `apps/api/src/core/config.py`（追加 NOTIFIER_TYPE / FEISHU_WEBHOOK_URL / TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID）
- Modify: `apps/api/.env.example`
- Create: `apps/api/tests/test_notifier.py`

**Interfaces:**
- Produces:
  - `async notify_pm(message: str) -> None`：根据 env NOTIFIER_TYPE 路由到 feishu/telegram/email/print

- [ ] **Step 1：扩 config**

`config.py` Settings 追加：
```python
notifier_type: str = "print"  # print | feishu | telegram | email
feishu_webhook_url: str = ""
telegram_bot_token: str = ""
telegram_chat_id: str = ""
```

`.env.example` 追加对应键。

- [ ] **Step 2：notifier.py**

```python
import httpx
from src.core.config import get_settings
from src.services.email_sender import send_email

async def notify_pm(message: str) -> None:
    s = get_settings()
    if s.notifier_type == "feishu" and s.feishu_webhook_url:
        async with httpx.AsyncClient() as c:
            await c.post(s.feishu_webhook_url, json={"msg_type": "text", "content": {"text": message}})
    elif s.notifier_type == "telegram" and s.telegram_bot_token and s.telegram_chat_id:
        url = f"https://api.telegram.org/bot{s.telegram_bot_token}/sendMessage"
        async with httpx.AsyncClient() as c:
            await c.post(url, json={"chat_id": s.telegram_chat_id, "text": message})
    elif s.notifier_type == "email" and s.smtp_host:
        send_email(to=s.smtp_from, subject="[JC] Coach Inquiry", html=f"<pre>{message}</pre>")
    else:
        print(f"[NOTIFY-PM] {message}")
```

- [ ] **Step 3：测试**

```python
import pytest
from unittest.mock import AsyncMock, patch
from src.services.notifier import notify_pm
from src.core import config

@pytest.mark.asyncio
async def test_print_mode_no_http(monkeypatch, capsys):
    monkeypatch.setenv("NOTIFIER_TYPE", "print")
    config.get_settings.cache_clear()
    await notify_pm("hello PM")
    out = capsys.readouterr().out
    assert "hello PM" in out

@pytest.mark.asyncio
async def test_feishu_mode_posts(monkeypatch):
    monkeypatch.setenv("NOTIFIER_TYPE", "feishu")
    monkeypatch.setenv("FEISHU_WEBHOOK_URL", "https://test.feishu/x")
    config.get_settings.cache_clear()
    with patch("httpx.AsyncClient.post", AsyncMock()) as mp:
        await notify_pm("ping")
        mp.assert_awaited_once()
```

Run: PASS

- [ ] **Step 4：提交**

```bash
git add apps/api && git commit -m "feat(api): notifier service (print/feishu/telegram/email)"
```

---

## Task 3: Coach Inquiry API

**Files:**
- Create: `apps/api/src/routers/coach.py`
- Create: `apps/api/src/schemas/coach.py`
- Modify: `apps/api/src/main.py`
- Create: `apps/api/tests/test_coach_api.py`

**Interfaces:**
- Produces:
  - `GET /api/v1/coach/availability` → `{slots_total: 5, slots_taken: int, available: bool, week_of: date}`
  - `POST /api/v1/coach/inquiries` body `{application_id?, source_screen, contact_method, notes?}` → 落库 + notify PM → 返回 `{id, available_after_create: bool}`

- [ ] **Step 1：schema**

```python
from datetime import date
from uuid import UUID
from pydantic import BaseModel

class CoachAvailability(BaseModel):
    week_of: date
    slots_total: int
    slots_taken: int
    available: bool

class CreateInquiryIn(BaseModel):
    application_id: UUID | None = None
    source_screen: str
    contact_method: str
    notes: str = ""

class CoachInquiryOut(BaseModel):
    id: UUID
    available_after_create: bool
```

- [ ] **Step 2：router**

`apps/api/src/routers/coach.py`：
```python
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.core.db import get_db
from src.core.deps import current_user
from src.models import User
from src.models.coach_inquiry import CoachInquiry, CoachInquiryStatus
from src.services.notifier import notify_pm
from src.services.time_helpers import monday_of, week_range, BJT
from src.schemas.coach import CoachAvailability, CreateInquiryIn, CoachInquiryOut

router = APIRouter(prefix="/api/v1/coach", tags=["coach"])

SLOTS_PER_WEEK = 5

def _taken_this_week(db: Session) -> int:
    m = monday_of(datetime.now(BJT))
    s, e = week_range(m)
    n = db.query(func.count(CoachInquiry.id)).filter(
        CoachInquiry.created_at >= s, CoachInquiry.created_at <= e,
        CoachInquiry.status != CoachInquiryStatus.DROPPED,
    ).scalar() or 0
    return n

@router.get("/availability", response_model=CoachAvailability)
def availability(db: Session = Depends(get_db)) -> CoachAvailability:
    m = monday_of(datetime.now(BJT))
    n = _taken_this_week(db)
    return CoachAvailability(week_of=m, slots_total=SLOTS_PER_WEEK, slots_taken=n, available=n < SLOTS_PER_WEEK)

@router.post("/inquiries", response_model=CoachInquiryOut, status_code=201)
async def create_inquiry(body: CreateInquiryIn, user: User = Depends(current_user), db: Session = Depends(get_db)) -> CoachInquiryOut:
    n = _taken_this_week(db)
    if n >= SLOTS_PER_WEEK:
        raise HTTPException(409, {"code": "coach_full", "message": "本周 Coach 名额已售罄，下周再约"})
    ci = CoachInquiry(user_id=user.id, application_id=body.application_id,
                      source_screen=body.source_screen, contact_method=body.contact_method, notes=body.notes)
    db.add(ci); db.commit(); db.refresh(ci)
    try:
        await notify_pm(f"🆕 Coach Inquiry\nuser={user.id}\ncontact={body.contact_method}\nsource={body.source_screen}\nnotes={body.notes}\napp_id={body.application_id}")
    except Exception:
        pass
    return CoachInquiryOut(id=ci.id, available_after_create=(n + 1 < SLOTS_PER_WEEK))
```

Modify main.py。

- [ ] **Step 3：测试**

`apps/api/tests/test_coach_api.py`：
```python
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from src.main import app
from src.core.security import issue_session_token
from src.core.db import SessionLocal
from src.models import User
from src.models.coach_inquiry import CoachInquiry

def _login():
    db = SessionLocal()
    u = User(preferences={}); db.add(u); db.commit(); db.refresh(u)
    c = TestClient(app); c.cookies.set("jc_session", issue_session_token(u.id))
    return c, db

def test_availability_starts_full_open():
    c, db = _login()
    db.query(CoachInquiry).delete(); db.commit()
    r = c.get("/api/v1/coach/availability")
    assert r.json()["available"] is True

def test_create_inquiry_notifies():
    c, db = _login()
    db.query(CoachInquiry).delete(); db.commit()
    with patch("src.routers.coach.notify_pm", AsyncMock()) as mp:
        r = c.post("/api/v1/coach/inquiries", json={"source_screen":"resume_workspace","contact_method":"wx:test"})
    assert r.status_code == 201
    mp.assert_awaited_once()

def test_capacity_full():
    c, db = _login()
    db.query(CoachInquiry).delete(); db.commit()
    with patch("src.routers.coach.notify_pm", AsyncMock()):
        for _ in range(5):
            c.post("/api/v1/coach/inquiries", json={"source_screen":"x","contact_method":"y"})
        r = c.post("/api/v1/coach/inquiries", json={"source_screen":"x","contact_method":"y"})
    assert r.status_code == 409
```

Run: PASS

- [ ] **Step 4：提交**

```bash
cd ../.. && git add apps/api && git commit -m "feat(api): coach availability + create inquiry + notifier integration"
```

---

## Task 4: Web — Coach Inquiry 完整表单（替换 Plan 3 占位）

**Files:**
- Modify: `apps/web/src/components/coach/CoachInquiryDrawer.tsx`（实化）
- Create: `apps/web/src/hooks/useCoach.ts`
- Create: `apps/web/src/app/[locale]/(app)/coach/page.tsx`
- Modify: `apps/web/messages/{zh,en}.json`

**Interfaces:**
- Produces:
  - `useCoachAvailability()` / `useCreateInquiry()`
  - 表单字段：联系方式（微信/手机/邮箱）+ 想被锐评的环节（自动带 application_id）+ 备注
  - 售罄状态下表单替换为"本周已满"+ 邮件订阅入口（v1 用 mailto）
  - `/coach` 一级页面：介绍 + 本周 slot 状态 + 进入表单

- [ ] **Step 1：翻译**

zh.json：
```json
"coach": {
  "title":"找 Coach 锐评",
  "intro":"1 对 1 真人 coach 给你简历做招聘方视角深度锐评，30-60 分钟。",
  "price":"¥500-2000 / 次",
  "slots_open":"本周还剩 {n} 个名额","slots_full":"本周名额已满，下周一早重置",
  "contact_label":"联系方式（微信号 / 手机 / 邮箱）",
  "notes_label":"想被锐评的环节（可选）",
  "submit":"提交申请",
  "submitted":"已提交，Coach 24h 内联系你",
  "subscribe_next_week":"留下邮箱，下周名额开放时通知我"
}
```

en.json 对应。

- [ ] **Step 2：hooks**

```typescript
'use client'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'

export function useCoachAvailability() {
  return useQuery({ queryKey: ['coach-availability'], queryFn: () => api<{ available: boolean; slots_total: number; slots_taken: number; week_of: string }>('/api/v1/coach/availability') })
}

export function useCreateInquiry() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { application_id?: string; source_screen: string; contact_method: string; notes?: string }) =>
      api<{ id: string; available_after_create: boolean }>('/api/v1/coach/inquiries', { method: 'POST', body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['coach-availability'] }),
  })
}
```

- [ ] **Step 3：替换 CoachInquiryDrawer 为完整表单**

```typescript
'use client'
import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { useCoachAvailability, useCreateInquiry } from '@/hooks/useCoach'

export function CoachInquiryDrawer({ appId, branchId, onClose, source = 'resume_workspace' }: { appId?: string; branchId?: string; onClose: () => void; source?: string }) {
  const t = useTranslations('coach')
  const { data: av } = useCoachAvailability()
  const create = useCreateInquiry()
  const [contact, setContact] = useState('')
  const [notes, setNotes] = useState('')
  const [done, setDone] = useState(false)

  async function submit() {
    await create.mutateAsync({ application_id: appId, source_screen: source, contact_method: contact, notes })
    setDone(true)
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center" onClick={onClose}>
      <div className="bg-white rounded p-6 w-[480px] space-y-3" onClick={(e) => e.stopPropagation()}>
        <h3 className="font-bold">{t('title')}</h3>
        <p className="text-sm">{t('intro')} · <b>{t('price')}</b></p>
        {av && (av.available
          ? <p className="text-xs text-green-700">{t('slots_open', { n: av.slots_total - av.slots_taken })}</p>
          : <p className="text-xs text-red-700">{t('slots_full')}</p>
        )}
        {!done && av?.available && (
          <>
            <input value={contact} onChange={(e) => setContact(e.target.value)} placeholder={t('contact_label')} className="w-full border rounded px-3 py-2" />
            <textarea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder={t('notes_label')} rows={3} className="w-full border rounded px-3 py-2" />
            <button onClick={submit} disabled={!contact || create.isPending} className="w-full bg-blue-600 text-white py-2 rounded disabled:opacity-50">
              {create.isPending ? '…' : t('submit')}
            </button>
          </>
        )}
        {done && <div className="text-green-700">✓ {t('submitted')}</div>}
        {!av?.available && (
          <a href="mailto:notify@example.com?subject=订阅Coach名额" className="block text-center text-sm text-blue-600 underline">{t('subscribe_next_week')}</a>
        )}
        <button onClick={onClose} className="w-full border py-2 rounded mt-2">关闭</button>
      </div>
    </div>
  )
}
```

> 注：原 `CoachInquiryButton`（Plan 3）保留，因为它现在打开的就是这个实化 Drawer。

- [ ] **Step 4：`/coach` 一级页面**

```typescript
'use client'
import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { useCoachAvailability } from '@/hooks/useCoach'
import { CoachInquiryDrawer } from '@/components/coach/CoachInquiryDrawer'

export default function CoachPage() {
  const t = useTranslations('coach')
  const { data: av } = useCoachAvailability()
  const [open, setOpen] = useState(false)
  return (
    <div className="max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold">{t('title')}</h1>
      <p>{t('intro')}</p>
      <p className="text-xl">{t('price')}</p>
      {av && (av.available
        ? <p className="text-green-700">{t('slots_open', { n: av.slots_total - av.slots_taken })}</p>
        : <p className="text-red-700">{t('slots_full')}</p>
      )}
      <button onClick={() => setOpen(true)} className="bg-blue-600 text-white px-6 py-3 rounded">
        {t('submit')}
      </button>
      {open && <CoachInquiryDrawer source="coach_page" onClose={() => setOpen(false)} />}
    </div>
  )
}
```

- [ ] **Step 5：提交**

```bash
git add apps/web && git commit -m "feat(web): full coach inquiry form (replaces Plan 3 placeholder) + /coach page"
```

---

## Task 5: 内部 Dashboard — Password 中间件

**Files:**
- Create: `apps/api/src/core/internal_auth.py`
- Modify: `apps/api/src/core/config.py`（追加 INTERNAL_DASHBOARD_PASSWORD）
- Modify: `apps/api/.env.example`
- Create: `apps/api/tests/test_internal_auth.py`

**Interfaces:**
- Produces:
  - 依赖 `require_internal_password(x_internal_password: Header)`：抛 401 if 不匹配

- [ ] **Step 1：config**

```python
internal_dashboard_password: str = ""
```
`.env.example` 追加。

- [ ] **Step 2：dep**

`apps/api/src/core/internal_auth.py`：
```python
from fastapi import Header, HTTPException
from src.core.config import get_settings

def require_internal_password(x_internal_password: str | None = Header(default=None)) -> None:
    expected = get_settings().internal_dashboard_password
    if not expected:
        raise HTTPException(503, "internal dashboard disabled (set INTERNAL_DASHBOARD_PASSWORD)")
    if x_internal_password != expected:
        raise HTTPException(401, "wrong internal password")
```

- [ ] **Step 3：测试**

```python
import pytest
from fastapi import HTTPException
from src.core.internal_auth import require_internal_password
from src.core import config

def test_rejects_wrong_password(monkeypatch):
    monkeypatch.setenv("INTERNAL_DASHBOARD_PASSWORD", "s3cret"); config.get_settings.cache_clear()
    with pytest.raises(HTTPException) as ei:
        require_internal_password(x_internal_password="wrong")
    assert ei.value.status_code == 401

def test_accepts_correct_password(monkeypatch):
    monkeypatch.setenv("INTERNAL_DASHBOARD_PASSWORD", "s3cret"); config.get_settings.cache_clear()
    require_internal_password(x_internal_password="s3cret")  # no raise
```

Run: PASS

- [ ] **Step 4：提交**

```bash
git add apps/api && git commit -m "feat(api): internal dashboard password middleware"
```

---

## Task 6: 内部 Dashboard API（聚合查询）

**Files:**
- Create: `apps/api/src/routers/internal_dashboard.py`
- Create: `apps/api/src/schemas/internal.py`
- Modify: `apps/api/src/main.py`
- Create: `apps/api/tests/test_internal_dashboard.py`

**Interfaces:**
- Produces:
  - `GET /internal/dashboard/summary` → `{dau, mau, total_users, ai_calls_today, ai_cost_today_usd, ai_cost_30d_usd, coach_inquiries_week}`
  - `GET /internal/dashboard/timeseries?days=30` → `{daily: [{date, dau, ai_calls, ai_cost}]}`
  - 都过 `require_internal_password`

- [ ] **Step 1：schema**

```python
from datetime import date
from pydantic import BaseModel

class DashboardSummary(BaseModel):
    dau: int; mau: int; total_users: int
    ai_calls_today: int; ai_cost_today_usd: float
    ai_calls_30d: int; ai_cost_30d_usd: float
    coach_inquiries_week: int

class DailyRow(BaseModel):
    date: date; dau: int; ai_calls: int; ai_cost: float

class TimeSeries(BaseModel):
    daily: list[DailyRow]
```

- [ ] **Step 2：router**

`apps/api/src/routers/internal_dashboard.py`：
```python
from datetime import date, datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from src.core.db import get_db
from src.core.internal_auth import require_internal_password
from src.models import User
from src.models.ai_call_log import AICallLog
from src.models.coach_inquiry import CoachInquiry
from src.services.time_helpers import monday_of, week_range, BJT
from src.schemas.internal import DashboardSummary, TimeSeries, DailyRow

router = APIRouter(prefix="/internal/dashboard", tags=["internal"], dependencies=[Depends(require_internal_password)])

@router.get("/summary", response_model=DashboardSummary)
def summary(db: Session = Depends(get_db)) -> DashboardSummary:
    now = datetime.now(timezone.utc)
    today_start = datetime.combine(now.date(), datetime.min.time(), tzinfo=timezone.utc)
    last_30 = now - timedelta(days=30)
    last_1 = now - timedelta(days=1)
    last_30d_active = db.query(func.count(func.distinct(User.id))).filter(User.last_active_at >= last_30).scalar() or 0
    dau = db.query(func.count(func.distinct(User.id))).filter(User.last_active_at >= last_1).scalar() or 0
    total = db.query(func.count(User.id)).scalar() or 0
    calls_today = db.query(func.count(AICallLog.id)).filter(AICallLog.created_at >= today_start).scalar() or 0
    cost_today = float(db.query(func.coalesce(func.sum(AICallLog.cost_usd), 0)).filter(AICallLog.created_at >= today_start).scalar() or 0)
    calls_30 = db.query(func.count(AICallLog.id)).filter(AICallLog.created_at >= last_30).scalar() or 0
    cost_30 = float(db.query(func.coalesce(func.sum(AICallLog.cost_usd), 0)).filter(AICallLog.created_at >= last_30).scalar() or 0)
    m = monday_of(datetime.now(BJT))
    ws, we = week_range(m)
    coach_week = db.query(func.count(CoachInquiry.id)).filter(CoachInquiry.created_at >= ws, CoachInquiry.created_at <= we).scalar() or 0
    return DashboardSummary(
        dau=dau, mau=last_30d_active, total_users=total,
        ai_calls_today=calls_today, ai_cost_today_usd=cost_today,
        ai_calls_30d=calls_30, ai_cost_30d_usd=cost_30,
        coach_inquiries_week=coach_week,
    )

@router.get("/timeseries", response_model=TimeSeries)
def timeseries(days: int = Query(30, ge=1, le=180), db: Session = Depends(get_db)) -> TimeSeries:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    # 按日聚合 ai_call_logs
    rows = db.query(
        cast(AICallLog.created_at, Date).label("d"),
        func.count(AICallLog.id).label("n"),
        func.coalesce(func.sum(AICallLog.cost_usd), 0).label("c"),
    ).filter(AICallLog.created_at >= since).group_by("d").all()
    by_d = {r.d: (r.n, float(r.c)) for r in rows}
    # 按日活跃用户：基于 last_active_at（不完美，但简化）
    daily: list[DailyRow] = []
    for i in range(days):
        d = (datetime.now(timezone.utc) - timedelta(days=days-1-i)).date()
        ds = datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc)
        de = ds + timedelta(days=1)
        dau = db.query(func.count(func.distinct(User.id))).filter(User.last_active_at >= ds, User.last_active_at < de).scalar() or 0
        n, c = by_d.get(d, (0, 0.0))
        daily.append(DailyRow(date=d, dau=dau, ai_calls=n, ai_cost=c))
    return TimeSeries(daily=daily)
```

Modify main.py 加入 internal_dashboard router。

- [ ] **Step 3：测试**

```python
from fastapi.testclient import TestClient
from src.main import app
from src.core import config

def test_dashboard_requires_password(monkeypatch):
    monkeypatch.setenv("INTERNAL_DASHBOARD_PASSWORD", "x"); config.get_settings.cache_clear()
    c = TestClient(app)
    r = c.get("/internal/dashboard/summary")
    assert r.status_code == 401

def test_dashboard_with_password_returns(monkeypatch):
    monkeypatch.setenv("INTERNAL_DASHBOARD_PASSWORD", "x"); config.get_settings.cache_clear()
    c = TestClient(app)
    r = c.get("/internal/dashboard/summary", headers={"X-Internal-Password": "x"})
    assert r.status_code == 200
    assert "dau" in r.json()
```

Run: PASS

- [ ] **Step 4：提交**

```bash
cd ../.. && git add apps/api && git commit -m "feat(api): internal dashboard summary + timeseries endpoints"
```

---

## Task 7: Web — 内部 Dashboard 页面（独立路由，4 张图）

**Files:**
- Create: `apps/web/src/app/internal/dashboard/page.tsx`（注意：不在 [locale] 下，无国际化）
- Create: `apps/web/src/components/internal/StatCards.tsx`
- Create: `apps/web/src/components/internal/SimpleChart.tsx`
- 修改 web 的 `middleware.ts` matcher 排除 `/internal`

**Interfaces:**
- Produces:
  - URL：`/internal/dashboard?password=xxx`（password 从 query 取，写入 sessionStorage 一次后省略）
  - 4 张图：DAU 折线 / AI 调用量折线 / 单 user 成本柱图 / 累计开销
  - 顶部 4 个 KPI 卡片

- [ ] **Step 1：修改 middleware**

`apps/web/middleware.ts`：
```typescript
export const config = {
  matcher: ['/((?!api|_next|internal|.*\\..*).*)'],
}
```

- [ ] **Step 2：SimpleChart（最小依赖：纯 SVG，避免装 chart 库）**

```typescript
'use client'
export function SimpleChart({ data, valueKey, label }: { data: any[]; valueKey: string; label: string }) {
  const max = Math.max(1, ...data.map((d) => Number(d[valueKey]) || 0))
  const W = 600, H = 120, pad = 24
  const x = (i: number) => pad + (i / Math.max(1, data.length - 1)) * (W - 2 * pad)
  const y = (v: number) => H - pad - (v / max) * (H - 2 * pad)
  const pts = data.map((d, i) => `${x(i)},${y(Number(d[valueKey]) || 0)}`).join(' ')
  return (
    <div className="border rounded p-3">
      <div className="text-xs text-gray-500 mb-1">{label} · max {max.toFixed(2)}</div>
      <svg width={W} height={H}>
        <polyline fill="none" stroke="#2563eb" strokeWidth={2} points={pts} />
        {data.map((d, i) => <circle key={i} cx={x(i)} cy={y(Number(d[valueKey]) || 0)} r={2} fill="#2563eb" />)}
      </svg>
    </div>
  )
}
```

- [ ] **Step 3：StatCards**

```typescript
'use client'
export function StatCards({ s }: { s: any }) {
  const cells = [
    { k:'DAU', v: s.dau },
    { k:'MAU', v: s.mau },
    { k:'Total Users', v: s.total_users },
    { k:'Coach 本周', v: s.coach_inquiries_week },
    { k:'AI 调用 (今日)', v: s.ai_calls_today },
    { k:'AI 成本 (今日)', v: `$${Number(s.ai_cost_today_usd).toFixed(2)}` },
    { k:'AI 调用 (30d)', v: s.ai_calls_30d },
    { k:'AI 成本 (30d)', v: `$${Number(s.ai_cost_30d_usd).toFixed(2)}` },
  ]
  return (
    <div className="grid grid-cols-4 gap-3">
      {cells.map((c) => (
        <div key={c.k} className="border rounded p-3 text-center">
          <div className="text-xs text-gray-500">{c.k}</div>
          <div className="text-2xl font-bold mt-1">{c.v}</div>
        </div>
      ))}
    </div>
  )
}
```

- [ ] **Step 4：page.tsx**

```typescript
'use client'
import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { StatCards } from '@/components/internal/StatCards'
import { SimpleChart } from '@/components/internal/SimpleChart'

const KEY = 'jc_internal_pwd'

export default function InternalDashboard() {
  const sp = useSearchParams()
  const [pwd, setPwd] = useState<string>('')
  const [summary, setSummary] = useState<any>(null)
  const [series, setSeries] = useState<any[]>([])
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    const q = sp.get('password')
    const stored = typeof window !== 'undefined' ? sessionStorage.getItem(KEY) : null
    setPwd(q ?? stored ?? '')
  }, [sp])

  useEffect(() => {
    if (!pwd) return
    sessionStorage.setItem(KEY, pwd)
    Promise.all([
      fetch(`${process.env.NEXT_PUBLIC_API_BASE}/internal/dashboard/summary`, { headers: { 'X-Internal-Password': pwd } }).then((r) => r.ok ? r.json() : Promise.reject('401')),
      fetch(`${process.env.NEXT_PUBLIC_API_BASE}/internal/dashboard/timeseries?days=30`, { headers: { 'X-Internal-Password': pwd } }).then((r) => r.ok ? r.json() : Promise.reject('401')),
    ]).then(([s, t]) => { setSummary(s); setSeries(t.daily) }).catch((e) => setErr(String(e)))
  }, [pwd])

  if (!pwd) {
    return (
      <main className="p-8">
        <input type="password" placeholder="internal password" onBlur={(e) => setPwd(e.target.value)} className="border rounded px-3 py-2" />
      </main>
    )
  }
  if (err) return <main className="p-8 text-red-700">{err}</main>
  if (!summary) return <main className="p-8">Loading…</main>

  return (
    <main className="p-6 space-y-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold">📊 Internal Dashboard</h1>
      <StatCards s={summary} />
      <SimpleChart data={series} valueKey="dau" label="DAU" />
      <SimpleChart data={series} valueKey="ai_calls" label="AI calls / day" />
      <SimpleChart data={series} valueKey="ai_cost" label="AI cost (USD) / day" />
    </main>
  )
}
```

- [ ] **Step 5：提交**

```bash
git add apps/web && git commit -m "feat(web): internal dashboard page with 4 KPI cards + 3 SVG charts"
```

---

## Task 8: Capacity Gates 接入 Coach Inquiry

**Files:**
- Modify: `apps/web/src/components/common/CapacityGate.tsx`（点击"找 Coach"打开 Drawer 而非跳 /coach）
- Modify: `apps/web/src/components/opportunities/NewOpportunityDialog.tsx`（capacity_monthly 时也走 Gate）

**Interfaces:**
- Produces：CapacityGate "找 Coach" 直接打开 CoachInquiryDrawer，source='capacity_gate'

- [ ] **Step 1**

```typescript
'use client'
import { useState } from 'react'
import { CoachInquiryDrawer } from '@/components/coach/CoachInquiryDrawer'

const MSG: Record<string, string> = {
  capacity_active: '你已经有 20 个进行中机会了，先归档一些再继续。',
  capacity_monthly: '30 天内新建机会数已达上限。要不要找 Coach 帮你聚焦？',
  capacity_resources: '资源数已达上限。',
  capacity_collections: '合集数已达上限。',
}

export function CapacityGate({ code, onClose }: { code: string; onClose: () => void }) {
  const [openCoach, setOpenCoach] = useState(false)
  if (openCoach) return <CoachInquiryDrawer source="capacity_gate" onClose={() => { setOpenCoach(false); onClose() }} />
  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center" onClick={onClose}>
      <div className="bg-white rounded p-6 w-96" onClick={(e) => e.stopPropagation()}>
        <h3 className="font-bold">温馨提示</h3>
        <p className="mt-2 text-sm">{MSG[code] ?? '已达使用上限'}</p>
        <div className="mt-4 flex justify-end gap-2">
          <button onClick={onClose} className="px-3 py-2">关闭</button>
          <button onClick={() => setOpenCoach(true)} className="px-4 py-2 bg-blue-600 text-white rounded">找 Coach</button>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2：提交**

```bash
git add apps/web && git commit -m "feat(web): capacity gate opens coach inquiry drawer directly"
```

---

## Task 9: PostHog + e2e

**Files:**
- Modify: `packages/shared-types/events.ts`
- Modify: hooks 加 track
- Create: `apps/web/e2e/coach.spec.ts`

- [ ] **Step 1**

```typescript
export const Events = {
  // ...
  COACH_INQUIRY_SUBMITTED: 'coach_inquiry_submitted',
  COACH_AVAILABILITY_VIEWED: 'coach_availability_viewed',
} as const
```

`useCreateInquiry` onSuccess → `track(Events.COACH_INQUIRY_SUBMITTED, { source })`。
`useCoachAvailability` 首次成功 → `track(Events.COACH_AVAILABILITY_VIEWED)`。

- [ ] **Step 2：e2e**

```typescript
import { test, expect } from '@playwright/test'

test('coach page renders', async ({ page }) => {
  await page.goto('/zh/coach')
  await expect(page.getByRole('heading', { name: '找 Coach 锐评' })).toBeVisible()
})

test('internal dashboard requires password', async ({ page }) => {
  await page.goto('/internal/dashboard')
  await expect(page.getByPlaceholder('internal password')).toBeVisible()
})
```

- [ ] **Step 3：提交**

```bash
git add packages apps && git commit -m "feat: posthog events + e2e for coach + internal dashboard"
```

---

## Plan 7 完成判定

```bash
pnpm --filter api test && pnpm --filter web typecheck && pnpm --filter web e2e
# 手动：
#   1) 简历页 → 点 "找 Coach 锐评" → 看到 slot 状态 → 填表提交 → notify 到飞书/邮件/print
#   2) 触发容量上限 → CapacityGate → "找 Coach" 一键打开同 Drawer
#   3) 浏览器开 /internal/dashboard?password=xxx → 看到 KPI + 3 张折线
```

---

## 🎯 v1 全套 7 个 Plan 完成

至此 Plan 0-7 全部产出（约 110+ tasks，500+ steps）：

| Plan | 模块 | tasks |
|---|---|---|
| 0 | 基础设施 + 项目骨架 | 17 |
| 1 | MasterResume | 14 |
| 2 | Application + JobPosting | 7 |
| 3 | ResumeBranch + PatchOperations | 14 |
| 4 | ResourceItem + Collection | 7 |
| 5 | Investment 投递记录 | 5 |
| 6 | WeeklyDigest 本周复盘 | 8 |
| 7 | Coach + 成本仪表盘 | 9 |
| **合计** | — | **81 tasks** |

按 plan 顺序执行，v1 总估时 16-18 周（个人独开）。
