# Plan 6：WeeklyDigest 本周复盘 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** "本周复盘"一级入口可用——展示本周统计（新增机会/定制版本/导出/Coach 咨询）+ AI 本周观察 + 建议下一步动作；支持周中任意时间打开（自动展示当前周或选择历史周）。

**Architecture:** WeeklyDigest 按 `week_of` 缓存；统计来自现有表 SQL；AI 观察基于 7 天活动数据（MiniMax-M1）；APScheduler 周一 00:30 预生成上周 digest。

**Tech Stack:** APScheduler 3.10+ / 复用前序

## Global Constraints
- 继承前序所有约束
- 周划分：周一 00:00 ~ 周日 23:59:59（UTC+8 北京时区）
- 缓存 key：`week_of = "YYYY-MM-DD"`（取本周一日期）
- AI 观察必须基于真实数据，不许编造
- 用户可手动触发"重算本周"

---

## Task 1: WeeklyDigest 模型 + 周划分工具

**Files:**
- Create: `apps/api/src/models/weekly_digest.py`
- Create: `apps/api/alembic/versions/0011_weekly_digest.py`
- Create: `apps/api/src/services/time_helpers.py`
- Create: `apps/api/tests/test_time_helpers.py`
- Modify: `apps/api/src/models/__init__.py`

**Interfaces:**
- Produces:
  - `WeeklyDigest(id, user_id, week_of [date], stats JSON, ai_observation_text, suggested_actions JSON, generated_at)`
  - `monday_of(now: datetime) -> date`（北京时区）
  - `week_range(monday: date) -> tuple[datetime, datetime]`

- [ ] **Step 1：模型**

`apps/api/src/models/weekly_digest.py`：
```python
from datetime import date, datetime
from uuid import uuid4, UUID
import sqlalchemy as sa
from sqlalchemy import JSON, Date, DateTime, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from src.core.db import Base

class WeeklyDigest(Base):
    __tablename__ = "weekly_digests"
    __table_args__ = (UniqueConstraint("user_id", "week_of", name="uq_user_week"),)
    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(sa.Uuid, index=True)
    week_of: Mapped[date] = mapped_column(Date, index=True)
    stats: Mapped[dict] = mapped_column(JSON, default=dict)
    ai_observation_text: Mapped[str] = mapped_column(Text, default="")
    suggested_actions: Mapped[list] = mapped_column(JSON, default=list)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=sa.func.now())
```

`__init__.py` 追加：`from src.models.weekly_digest import WeeklyDigest  # noqa`

- [ ] **Step 2：迁移**

```bash
cd apps/api && source .venv/bin/activate
alembic revision --autogenerate -m "weekly digest"
alembic upgrade head
```

- [ ] **Step 3：time_helpers**

```python
from datetime import datetime, date, timedelta, timezone
from zoneinfo import ZoneInfo

BJT = ZoneInfo("Asia/Shanghai")

def monday_of(now: datetime | None = None) -> date:
    n = (now or datetime.now(BJT)).astimezone(BJT)
    return (n - timedelta(days=n.weekday())).date()

def week_range(monday: date) -> tuple[datetime, datetime]:
    start = datetime.combine(monday, datetime.min.time(), tzinfo=BJT)
    end = start + timedelta(days=7) - timedelta(microseconds=1)
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)
```

- [ ] **Step 4：测试**

`tests/test_time_helpers.py`：
```python
from datetime import datetime
from zoneinfo import ZoneInfo
from src.services.time_helpers import monday_of, week_range

BJT = ZoneInfo("Asia/Shanghai")

def test_monday_of_wednesday():
    d = datetime(2026, 6, 24, 12, 0, tzinfo=BJT)   # 2026-06-24 is Wednesday
    m = monday_of(d)
    assert m.isoformat() == "2026-06-22"

def test_week_range_spans_seven_days():
    s, e = week_range(datetime(2026, 6, 22).date())
    assert (e - s).days == 6
```

Run: PASS

- [ ] **Step 5：提交**

```bash
cd ../.. && git add apps/api && git commit -m "feat(api): WeeklyDigest model + Beijing-tz week helpers"
```

---

## Task 2: 统计计算 Service

**Files:**
- Create: `apps/api/src/services/weekly_stats.py`
- Create: `apps/api/tests/test_weekly_stats.py`

**Interfaces:**
- Produces:
  - `compute_stats(db, user_id: UUID, monday: date) -> dict`：返回 `{new_applications, new_branches, exports, coach_inquiries, total_active_applications}`

- [ ] **Step 1：service**

```python
from datetime import date
from uuid import UUID
from sqlalchemy import func
from sqlalchemy.orm import Session
from src.models import Application, ApplicationStatus, ResumeBranch
from src.services.time_helpers import week_range

def compute_stats(db: Session, user_id: UUID, monday: date) -> dict:
    start, end = week_range(monday)
    new_apps = db.query(func.count(Application.id)).filter(
        Application.user_id == user_id,
        Application.created_at >= start, Application.created_at <= end,
    ).scalar() or 0

    new_branches = db.query(func.count(ResumeBranch.id)).join(
        Application, Application.id == ResumeBranch.application_id
    ).filter(
        Application.user_id == user_id,
        ResumeBranch.created_at >= start, ResumeBranch.created_at <= end,
    ).scalar() or 0

    # exports：统计 exported_pdf_urls 长度增量过于复杂，简化为本周新建分支的导出数
    rows = db.query(ResumeBranch).join(Application).filter(
        Application.user_id == user_id,
        ResumeBranch.created_at >= start, ResumeBranch.created_at <= end,
    ).all()
    exports = sum(len(r.exported_pdf_urls or []) for r in rows)

    # coach_inquiries（Plan 7 表）：可能不存在，try
    coach_inquiries = 0
    try:
        from src.models.coach_inquiry import CoachInquiry
        coach_inquiries = db.query(func.count(CoachInquiry.id)).filter(
            CoachInquiry.user_id == user_id,
            CoachInquiry.created_at >= start, CoachInquiry.created_at <= end,
        ).scalar() or 0
    except ImportError:
        pass

    total_active = db.query(func.count(Application.id)).filter(
        Application.user_id == user_id, Application.status != ApplicationStatus.ARCHIVED,
    ).scalar() or 0

    return {
        "new_applications": new_apps,
        "new_branches": new_branches,
        "exports": exports,
        "coach_inquiries": coach_inquiries,
        "total_active_applications": total_active,
    }
```

- [ ] **Step 2：测试**

```python
from datetime import datetime, timezone
from src.services.weekly_stats import compute_stats
from src.services.time_helpers import monday_of, BJT
from src.models import User, Application, JobPosting

def test_stats_counts_new_apps(db):
    u = User(preferences={}); db.add(u); db.flush()
    a = Application(user_id=u.id); a.job_posting = JobPosting(raw_text="x")
    db.add(a); db.commit()
    m = monday_of(datetime.now(BJT))
    s = compute_stats(db, u.id, m)
    assert s["new_applications"] >= 1
    assert s["total_active_applications"] >= 1
```

Run: PASS

- [ ] **Step 3：提交**

```bash
git add apps/api && git commit -m "feat(api): weekly stats computation across apps/branches/exports/coach"
```

---

## Task 3: AI 本周观察 Service

**Files:**
- Create: `apps/api/src/ai/prompts/weekly_observation.py`
- Create: `apps/api/src/services/weekly_observer.py`
- Create: `apps/api/tests/test_weekly_observer.py`

**Interfaces:**
- Produces:
  - `async generate_observation(stats: dict, sample_jds: list[dict], user_id: UUID) -> {text, suggested_actions: [{label, url?}]}`
  - sample_jds：本周新建机会的 JD 摘要列表（公司+岗位+硬技能 top 3），用于 AI 看趋势

- [ ] **Step 1：prompt**

```python
WEEKLY_OBSERVATION_SYSTEM = """你是求职数据分析师。基于"本周统计 + 新增机会的 JD 摘要"，输出严格 JSON：
{
  "text": "1-3 句中文观察（必须具体到数字与方向，禁止鸡汤）",
  "suggested_actions": [{"label": "具体行动", "url": null}]
}
- 观察示例：「这周新增 4 个机会，75% 集中在『增长 + B2C』方向，但主简历『数据驱动』维度只有 1 条强证据，建议补强」
- 行动 1-3 条，必须可执行
- 仅 JSON
"""
```

- [ ] **Step 2：service**

```python
import json
from uuid import UUID
from sqlalchemy.orm import Session
from src.ai.llm_client import LLMClient
from src.ai.prompts.weekly_observation import WEEKLY_OBSERVATION_SYSTEM

_llm = LLMClient()

async def generate_observation(stats: dict, sample_jds: list[dict], user_id: UUID) -> dict:
    payload = {"stats": stats, "new_jds": sample_jds}
    raw = await _llm.acomplete(
        model="auto-m1",
        system=WEEKLY_OBSERVATION_SYSTEM,
        messages=[{"role":"user","content": json.dumps(payload, ensure_ascii=False)}],
        max_tokens=512, user_id=user_id, scene="weekly_observation",
    )
    return json.loads(raw)
```

- [ ] **Step 3：测试**

```python
import json
from unittest.mock import patch, AsyncMock
from uuid import uuid4
import pytest
from src.services.weekly_observer import generate_observation

@pytest.mark.asyncio
async def test_observation():
    fake = {"text":"本周 75% 在增长方向","suggested_actions":[{"label":"补强数据卡","url": None}]}
    with patch("src.services.weekly_observer._llm.acomplete", AsyncMock(return_value=json.dumps(fake))):
        out = await generate_observation({"new_applications": 4}, [{"company":"字节"}], uuid4())
    assert "增长" in out["text"]
```

Run: PASS

- [ ] **Step 4：提交**

```bash
git add apps/api && git commit -m "feat(api): AI weekly observation generator + suggested actions"
```

---

## Task 4: WeeklyDigest 生成 + Get/Refresh 服务

**Files:**
- Create: `apps/api/src/services/weekly_digester.py`
- Create: `apps/api/tests/test_weekly_digester.py`

**Interfaces:**
- Produces:
  - `async get_or_create(db, user_id, monday: date | None = None, force_refresh: bool = False) -> WeeklyDigest`

- [ ] **Step 1：service**

```python
from datetime import datetime, date
from uuid import UUID
from sqlalchemy.orm import Session
from src.models.weekly_digest import WeeklyDigest
from src.models import Application
from src.services.weekly_stats import compute_stats
from src.services.weekly_observer import generate_observation
from src.services.time_helpers import monday_of, week_range, BJT

async def get_or_create(db: Session, user_id: UUID, monday: date | None = None, force_refresh: bool = False) -> WeeklyDigest:
    m = monday or monday_of(datetime.now(BJT))
    existing = db.query(WeeklyDigest).filter(WeeklyDigest.user_id == user_id, WeeklyDigest.week_of == m).first()
    if existing and not force_refresh:
        return existing

    stats = compute_stats(db, user_id, m)
    start, end = week_range(m)
    new_jds = []
    rows = db.query(Application).filter(
        Application.user_id == user_id,
        Application.created_at >= start, Application.created_at <= end,
    ).all()
    for a in rows:
        jp = a.job_posting
        if not jp: continue
        new_jds.append({
            "company": jp.company_name, "title": jp.job_title,
            "hard_skills_top": (jp.requirements_parsed or {}).get("hard", [])[:3],
        })

    try:
        ai_out = await generate_observation(stats, new_jds, user_id)
        text, actions = ai_out.get("text", ""), ai_out.get("suggested_actions", [])
    except Exception as e:
        text, actions = f"本周共 {stats['new_applications']} 个新机会、{stats['new_branches']} 个简历版本。（AI 观察暂不可用：{e}）", []

    if existing:
        existing.stats = stats; existing.ai_observation_text = text; existing.suggested_actions = actions
    else:
        existing = WeeklyDigest(user_id=user_id, week_of=m, stats=stats,
                                ai_observation_text=text, suggested_actions=actions)
        db.add(existing)
    db.commit(); db.refresh(existing)
    return existing
```

- [ ] **Step 2：测试**

```python
from unittest.mock import patch, AsyncMock
import pytest
from src.services.weekly_digester import get_or_create
from src.models import User

@pytest.mark.asyncio
async def test_creates_when_missing(db):
    u = User(preferences={}); db.add(u); db.commit(); db.refresh(u)
    with patch("src.services.weekly_digester.generate_observation",
               AsyncMock(return_value={"text":"x", "suggested_actions":[]})):
        d = await get_or_create(db, u.id)
    assert d.ai_observation_text == "x"
```

Run: PASS

- [ ] **Step 3：提交**

```bash
git add apps/api && git commit -m "feat(api): WeeklyDigest get_or_create with caching + force refresh"
```

---

## Task 5: WeeklyDigest API

**Files:**
- Create: `apps/api/src/routers/weekly.py`
- Create: `apps/api/src/schemas/weekly.py`
- Modify: `apps/api/src/main.py`
- Create: `apps/api/tests/test_weekly_api.py`

**Interfaces:**
- Produces:
  - `GET /api/v1/weekly?week_of=YYYY-MM-DD` → 当周 digest，无则即时生成
  - `POST /api/v1/weekly/refresh?week_of=YYYY-MM-DD` → 强制重算
  - `GET /api/v1/weekly/history?weeks=8` → 最近 N 周列表（仅 stats 摘要）

- [ ] **Step 1：schema**

```python
from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel

class WeeklyOut(BaseModel):
    id: UUID
    week_of: date
    stats: dict
    ai_observation_text: str
    suggested_actions: list[dict]
    generated_at: datetime

class WeeklyHistoryItem(BaseModel):
    week_of: date
    stats: dict
```

- [ ] **Step 2：router**

```python
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from src.core.db import get_db
from src.core.deps import current_user
from src.models import User
from src.models.weekly_digest import WeeklyDigest
from src.services.weekly_digester import get_or_create
from src.services.time_helpers import monday_of, BJT
from src.schemas.weekly import WeeklyOut, WeeklyHistoryItem

router = APIRouter(prefix="/api/v1/weekly", tags=["weekly"])

def _parse(week_of: str | None) -> date | None:
    return date.fromisoformat(week_of) if week_of else None

@router.get("", response_model=WeeklyOut)
async def get_weekly(week_of: str | None = None, user: User = Depends(current_user), db: Session = Depends(get_db)) -> WeeklyOut:
    d = await get_or_create(db, user.id, _parse(week_of), force_refresh=False)
    return WeeklyOut(id=d.id, week_of=d.week_of, stats=d.stats,
                     ai_observation_text=d.ai_observation_text,
                     suggested_actions=d.suggested_actions, generated_at=d.generated_at)

@router.post("/refresh", response_model=WeeklyOut)
async def refresh_weekly(week_of: str | None = None, user: User = Depends(current_user), db: Session = Depends(get_db)) -> WeeklyOut:
    d = await get_or_create(db, user.id, _parse(week_of), force_refresh=True)
    return WeeklyOut(id=d.id, week_of=d.week_of, stats=d.stats,
                     ai_observation_text=d.ai_observation_text,
                     suggested_actions=d.suggested_actions, generated_at=d.generated_at)

@router.get("/history", response_model=list[WeeklyHistoryItem])
def history(weeks: int = Query(8, ge=1, le=52), user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[WeeklyHistoryItem]:
    rows = db.query(WeeklyDigest).filter(WeeklyDigest.user_id == user.id) \
              .order_by(WeeklyDigest.week_of.desc()).limit(weeks).all()
    return [WeeklyHistoryItem(week_of=r.week_of, stats=r.stats) for r in rows]
```

Modify main.py include。

- [ ] **Step 3：测试**

```python
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from src.main import app
from src.core.security import issue_session_token
from src.core.db import SessionLocal
from src.models import User

def test_get_weekly_returns():
    db = SessionLocal()
    u = User(preferences={}); db.add(u); db.commit(); db.refresh(u)
    c = TestClient(app); c.cookies.set("jc_session", issue_session_token(u.id))
    with patch("src.services.weekly_digester.generate_observation",
               AsyncMock(return_value={"text":"ok","suggested_actions":[]})):
        r = c.get("/api/v1/weekly")
    assert r.status_code == 200
    assert "ai_observation_text" in r.json()
```

Run: PASS

- [ ] **Step 4：提交**

```bash
cd ../.. && git add apps/api && git commit -m "feat(api): weekly digest endpoints (get/refresh/history)"
```

---

## Task 6: APScheduler Cron 周一预生成

**Files:**
- Create: `apps/api/src/jobs/__init__.py`
- Create: `apps/api/src/jobs/scheduler.py`
- Modify: `apps/api/src/main.py`（startup hook）
- Modify: `apps/api/pyproject.toml`（加 apscheduler）
- Create: `apps/api/tests/test_scheduler.py`

**Interfaces:**
- Produces:
  - APScheduler AsyncIOScheduler 在 app startup 启动
  - 任务：每周一 00:30 BJT，遍历所有用户 → 调 `get_or_create(force_refresh=True, monday=prev_monday)`

- [ ] **Step 1：装依赖**

```bash
cd apps/api && source .venv/bin/activate
pip install apscheduler==3.10.4
```
`pyproject.toml` 追加：`"apscheduler==3.10.4",`

- [ ] **Step 2：scheduler.py**

```python
from datetime import date, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from src.core.db import SessionLocal
from src.models import User
from src.services.weekly_digester import get_or_create
from src.services.time_helpers import monday_of, BJT
from datetime import datetime

scheduler = AsyncIOScheduler(timezone=BJT)

async def regenerate_all_users_prev_week() -> None:
    """周一 00:30 BJT 触发：为所有 user 重算"上周"digest"""
    prev_monday = monday_of(datetime.now(BJT)) - timedelta(days=7)
    db: Session = SessionLocal()
    try:
        ids = [r[0] for r in db.query(User.id).all()]
        for uid in ids:
            try:
                await get_or_create(db, uid, prev_monday, force_refresh=True)
            except Exception:
                continue
    finally:
        db.close()

def start_scheduler() -> None:
    if scheduler.running:
        return
    scheduler.add_job(
        regenerate_all_users_prev_week,
        CronTrigger(day_of_week="mon", hour=0, minute=30, timezone=BJT),
        id="weekly_digest_regen",
        replace_existing=True,
    )
    scheduler.start()

def shutdown_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
```

- [ ] **Step 3：main.py startup hook**

修改 `apps/api/src/main.py`：
```python
from contextlib import asynccontextmanager
from src.jobs.scheduler import start_scheduler, shutdown_scheduler

@asynccontextmanager
async def lifespan(app):
    start_scheduler()
    yield
    shutdown_scheduler()

app = FastAPI(title="Job Companion API", version="0.0.0", lifespan=lifespan)
# ... include routers as before
```

- [ ] **Step 4：测试**

```python
from src.jobs.scheduler import scheduler, start_scheduler

def test_scheduler_starts_and_registers_job():
    start_scheduler()
    jobs = scheduler.get_jobs()
    assert any(j.id == "weekly_digest_regen" for j in jobs)
    scheduler.remove_job("weekly_digest_regen")
```

Run: PASS

- [ ] **Step 5：提交**

```bash
cd ../.. && git add apps/api && git commit -m "feat(api): APScheduler weekly digest cron (Monday 00:30 BJT)"
```

---

## Task 7: Web — Weekly Recap Hooks + Page

**Files:**
- Create: `apps/web/src/hooks/useWeekly.ts`
- Modify: `apps/web/src/app/[locale]/(app)/weekly/page.tsx`
- Create: `apps/web/src/components/weekly/StatGrid.tsx`
- Create: `apps/web/src/components/weekly/ObservationCard.tsx`
- Create: `apps/web/src/components/weekly/WeekPicker.tsx`
- Modify: `apps/web/messages/{zh,en}.json`

**Interfaces:**
- Produces:
  - Stats 卡片网格（新增机会 / 定制版本 / 导出 / Coach 询问）
  - AI 观察卡片（含建议下一步按钮）
  - 周选择器（默认本周，可选历史 8 周）
  - 顶部"🔄 重算本周"按钮

- [ ] **Step 1：hooks**

```typescript
'use client'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'

export function useWeekly(weekOf?: string) {
  return useQuery({
    queryKey: ['weekly', weekOf],
    queryFn: () => api<any>(`/api/v1/weekly${weekOf ? `?week_of=${weekOf}` : ''}`),
  })
}

export function useRefreshWeekly() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (weekOf?: string) => api(`/api/v1/weekly/refresh${weekOf ? `?week_of=${weekOf}` : ''}`, { method: 'POST' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['weekly'] }),
  })
}

export function useWeeklyHistory(weeks = 8) {
  return useQuery({ queryKey: ['weekly-history', weeks], queryFn: () => api<any[]>(`/api/v1/weekly/history?weeks=${weeks}`) })
}
```

- [ ] **Step 2：翻译**

zh.json：
```json
"weekly": {
  "title":"本周复盘","refresh":"🔄 重算",
  "stat_new_applications":"新增机会","stat_new_branches":"定制版本","stat_exports":"导出 PDF","stat_coach_inquiries":"Coach 咨询",
  "stat_total_active":"进行中机会",
  "observation":"📈 AI 本周观察","actions":"建议下一步",
  "pick_week":"选择周次","history":"历史"
}
```

- [ ] **Step 3：StatGrid**

```typescript
'use client'
import { useTranslations } from 'next-intl'

export function StatGrid({ stats }: { stats: any }) {
  const t = useTranslations('weekly')
  const cells = [
    { k: 'new_applications', v: stats.new_applications ?? 0 },
    { k: 'new_branches', v: stats.new_branches ?? 0 },
    { k: 'exports', v: stats.exports ?? 0 },
    { k: 'coach_inquiries', v: stats.coach_inquiries ?? 0 },
    { k: 'total_active', v: stats.total_active_applications ?? 0 },
  ]
  return (
    <div className="grid grid-cols-5 gap-3">
      {cells.map((c) => (
        <div key={c.k} className="border rounded p-4 text-center">
          <div className="text-3xl font-bold">{c.v}</div>
          <div className="text-xs text-gray-500 mt-1">{t(`stat_${c.k}` as any)}</div>
        </div>
      ))}
    </div>
  )
}
```

- [ ] **Step 4：ObservationCard**

```typescript
'use client'
import Link from 'next/link'
import { useTranslations } from 'next-intl'
import { useParams } from 'next/navigation'

export function ObservationCard({ text, actions }: { text: string; actions: { label: string; url?: string | null }[] }) {
  const t = useTranslations('weekly')
  const { locale } = useParams<{ locale: string }>()
  if (!text) return null
  return (
    <div className="border rounded p-4 bg-gradient-to-br from-blue-50 to-white">
      <h3 className="font-bold text-sm">{t('observation')}</h3>
      <p className="text-base mt-2 leading-relaxed">{text}</p>
      {actions?.length > 0 && (
        <>
          <h4 className="text-xs text-gray-500 mt-3">{t('actions')}</h4>
          <div className="flex gap-2 mt-1 flex-wrap">
            {actions.map((a, i) => (
              a.url
                ? <Link key={i} href={a.url.startsWith('/') ? `/${locale}${a.url}` : a.url} className="text-sm border border-blue-600 text-blue-600 rounded px-3 py-1">{a.label}</Link>
                : <span key={i} className="text-sm border rounded px-3 py-1">{a.label}</span>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
```

- [ ] **Step 5：WeekPicker**

```typescript
'use client'
import { useWeeklyHistory } from '@/hooks/useWeekly'

export function WeekPicker({ value, onChange }: { value: string | undefined; onChange: (v: string | undefined) => void }) {
  const { data } = useWeeklyHistory(12)
  return (
    <select value={value ?? ''} onChange={(e) => onChange(e.target.value || undefined)} className="border rounded px-3 py-1 text-sm">
      <option value="">本周</option>
      {(data ?? []).map((h: any) => <option key={h.week_of} value={h.week_of}>{h.week_of}</option>)}
    </select>
  )
}
```

- [ ] **Step 6：page.tsx**

```typescript
'use client'
import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { useWeekly, useRefreshWeekly } from '@/hooks/useWeekly'
import { StatGrid } from '@/components/weekly/StatGrid'
import { ObservationCard } from '@/components/weekly/ObservationCard'
import { WeekPicker } from '@/components/weekly/WeekPicker'

export default function WeeklyPage() {
  const t = useTranslations('weekly')
  const [weekOf, setWeekOf] = useState<string | undefined>(undefined)
  const { data } = useWeekly(weekOf)
  const refresh = useRefreshWeekly()

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{t('title')}</h1>
        <div className="flex items-center gap-2">
          <WeekPicker value={weekOf} onChange={setWeekOf} />
          <button onClick={() => refresh.mutate(weekOf)} disabled={refresh.isPending}
                  className="px-3 py-1 text-sm bg-black text-white rounded disabled:opacity-50">
            {refresh.isPending ? '…' : t('refresh')}
          </button>
        </div>
      </div>
      {data && (
        <>
          <StatGrid stats={data.stats ?? {}} />
          <ObservationCard text={data.ai_observation_text} actions={data.suggested_actions ?? []} />
        </>
      )}
    </div>
  )
}
```

- [ ] **Step 7：提交**

```bash
git add apps/web && git commit -m "feat(web): weekly recap page with stats + AI observation + week picker"
```

---

## Task 8: PostHog + e2e

**Files:**
- Modify: `packages/shared-types/events.ts`
- Modify: `apps/web/src/hooks/useWeekly.ts`（onSuccess track）
- Create: `apps/web/e2e/weekly.spec.ts`

- [ ] **Step 1**

```typescript
export const Events = {
  // ...
  WEEKLY_OPENED: 'weekly_opened',
  WEEKLY_REFRESHED: 'weekly_refreshed',
  WEEKLY_ACTION_CLICKED: 'weekly_action_clicked',
} as const
```

`useRefreshWeekly` onSuccess track。

`apps/web/src/components/weekly/ObservationCard.tsx` 顶部加 useEffect track WEEKLY_OPENED 一次。

- [ ] **Step 2：e2e**

```typescript
import { test, expect } from '@playwright/test'

test('weekly page renders header and picker', async ({ page }) => {
  await page.goto('/zh/weekly')
  await expect(page.getByRole('heading', { name: '本周复盘' })).toBeVisible()
})
```

- [ ] **Step 3：提交**

```bash
git add packages apps && git commit -m "feat: posthog events + e2e for weekly recap"
```

---

## Plan 6 完成判定

```bash
pnpm --filter api test && pnpm --filter web typecheck && pnpm --filter web e2e
# 手动：/zh/weekly → 看到 stats 网格 + AI 观察文字 + 建议按钮；切换历史周；点重算；APScheduler 在后台跑（周一 00:30 触发）
```

下一站 → Plan 7 (Coach + 成本仪表盘)
