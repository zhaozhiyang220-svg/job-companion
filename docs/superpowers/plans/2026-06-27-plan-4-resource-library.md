# Plan 4：ResourceItem + Collection 模块 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 用户能把面经/公司情报/招聘者背景/行业资料等"求职原料"沉淀到资源库；可分合集管理；可关联到具体求职机会；AI 自动摘要 + 提取"对简历/面试有用的信号"。

**Architecture:** ResourceItem 为横向数据层（不属于任何机会，但可多对多关联）；ResourceCollection 为可选分组；AI 摘要单独服务（abab6.5s-chat / MiniMax 轻档）；与 Plan 2 的 application_resource_links 表对接 FK。

**Tech Stack:** 复用前序

## Global Constraints
- 继承前序所有约束
- 容量：≤ 100 资源 / ≤ 5 合集（超限走 CapacityGate）
- 资源类型枚举：`interview_recall`（面经）/ `company_intel`（公司情报）/ `recruiter_bg`（招聘者背景）/ `industry_doc`（行业资料）/ `other`

---

## Task 1: ResourceItem + ResourceCollection 模型

**Files:**
- Create: `apps/api/src/models/resource_item.py`
- Create: `apps/api/src/models/resource_collection.py`
- Create: `apps/api/src/models/resource_collection_link.py`
- Create: `apps/api/alembic/versions/0009_resources.py`
- Modify: `apps/api/src/models/__init__.py`
- Create: `apps/api/tests/test_resource_models.py`

**Interfaces:**
- Produces:
  - `ResourceItem(id, user_id, type, title, content_text, source_url, attachments JSON, tags JSON, ai_summary, ai_extracted_signals JSON, linked_company_names JSON, created_at)`
  - `ResourceCollection(id, user_id, name, description, created_at)`
  - `ResourceCollectionLink(collection_id, resource_id)` 多对多
  - 同时补 FK：`application_resource_links.resource_item_id → resource_items.id`

- [ ] **Step 1：模型**

`apps/api/src/models/resource_item.py`：
```python
from datetime import datetime
from enum import StrEnum
from uuid import uuid4, UUID
import sqlalchemy as sa
from sqlalchemy import String, DateTime, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column
from src.core.db import Base

class ResourceType(StrEnum):
    INTERVIEW_RECALL = "interview_recall"
    COMPANY_INTEL = "company_intel"
    RECRUITER_BG = "recruiter_bg"
    INDUSTRY_DOC = "industry_doc"
    OTHER = "other"

class ResourceItem(Base):
    __tablename__ = "resource_items"
    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(sa.Uuid, index=True)
    type: Mapped[ResourceType] = mapped_column(sa.Enum(ResourceType, name="resource_type_enum"), default=ResourceType.OTHER, index=True)
    title: Mapped[str] = mapped_column(String(256))
    content_text: Mapped[str] = mapped_column(Text, default="")
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    attachments: Mapped[list] = mapped_column(JSON, default=list)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    ai_summary: Mapped[str] = mapped_column(Text, default="")
    ai_extracted_signals: Mapped[list] = mapped_column(JSON, default=list)
    linked_company_names: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=sa.func.now())
```

`apps/api/src/models/resource_collection.py`：
```python
from datetime import datetime
from uuid import uuid4, UUID
import sqlalchemy as sa
from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from src.core.db import Base

class ResourceCollection(Base):
    __tablename__ = "resource_collections"
    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(sa.Uuid, index=True)
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=sa.func.now())
```

`apps/api/src/models/resource_collection_link.py`：
```python
from uuid import UUID
import sqlalchemy as sa
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from src.core.db import Base

class ResourceCollectionLink(Base):
    __tablename__ = "resource_collection_links"
    collection_id: Mapped[UUID] = mapped_column(sa.Uuid, ForeignKey("resource_collections.id"), primary_key=True)
    resource_id: Mapped[UUID] = mapped_column(sa.Uuid, ForeignKey("resource_items.id"), primary_key=True)
```

`__init__.py` 追加 4 行 import。

- [ ] **Step 2：迁移（含补 FK）**

```bash
cd apps/api && source .venv/bin/activate
alembic revision --autogenerate -m "resources + collections + link + FK on application_resource_links"
```

打开生成的 migration，在 upgrade() 中追加 FK 修复：
```python
op.create_foreign_key(
    "fk_application_resource_links_resource_item_id",
    "application_resource_links", "resource_items",
    ["resource_item_id"], ["id"],
    ondelete="CASCADE",
)
```

`downgrade()` 对应 drop。
```bash
alembic upgrade head
```

- [ ] **Step 3：测试**

`apps/api/tests/test_resource_models.py`：
```python
from src.models import User
from src.models.resource_item import ResourceItem, ResourceType
from src.models.resource_collection import ResourceCollection
from src.models.resource_collection_link import ResourceCollectionLink

def test_create_resource_and_collection(db):
    u = User(preferences={}); db.add(u); db.flush()
    coll = ResourceCollection(user_id=u.id, name="字节面试")
    res = ResourceItem(user_id=u.id, type=ResourceType.INTERVIEW_RECALL,
                       title="豆包 PM 二面面经", content_text="...")
    db.add_all([coll, res]); db.flush()
    db.add(ResourceCollectionLink(collection_id=coll.id, resource_id=res.id)); db.flush()
    assert res.type == ResourceType.INTERVIEW_RECALL
    assert coll.name == "字节面试"
```

Run: PASS

- [ ] **Step 4：提交**

```bash
cd ../.. && git add apps/api && git commit -m "feat(api): ResourceItem + ResourceCollection + link + FK fix"
```

---

## Task 2: AI 资源摘要 + 信号提取 Service

**Files:**
- Create: `apps/api/src/ai/prompts/summarize_resource.py`
- Create: `apps/api/src/services/resource_processor.py`
- Create: `apps/api/tests/test_resource_processor.py`

**Interfaces:**
- Produces:
  - `async summarize(text: str, type: ResourceType, user_id: UUID) -> {summary: str, signals: list[{type, content}], companies: list[str]}`
  - signal type 例：`question_pattern`（面试官常问）/ `culture_signal`（公司文化）/ `process_step`（流程节点）/ `salary_anchor`（薪资锚点）

- [ ] **Step 1：prompt**

```python
SUMMARIZE_RESOURCE_SYSTEM = """你是求职情报分析师。读一段求职原料（面经/公司情报/招聘者背景/行业资料），输出严格 JSON：
{
  "summary": "1-3 句中文摘要",
  "signals": [{"type":"question_pattern|culture_signal|process_step|salary_anchor|other","content":"具体信号一句话"}],
  "companies": ["可识别的公司名"]
}
- signals 最多 5 条，只挑对"调整简历 / 准备面试 / 谈薪"真有用的
- companies 不许编造，未提到留空数组
- 仅 JSON
"""
```

- [ ] **Step 2：service**

```python
import json
from uuid import UUID
from src.ai.llm_client import LLMClient
from src.ai.prompts.summarize_resource import SUMMARIZE_RESOURCE_SYSTEM
from src.models.resource_item import ResourceType

_llm = LLMClient()

async def summarize(text: str, type_: ResourceType, user_id: UUID) -> dict:
    raw = await _llm.acomplete(
        model="auto-light",
        system=SUMMARIZE_RESOURCE_SYSTEM,
        messages=[{"role":"user","content": f"类型：{type_.value}\n\n原文：\n{text[:6000]}"}],
        max_tokens=512, user_id=user_id, scene="resource_summarize",
    )
    return json.loads(raw)
```

- [ ] **Step 3：测试**

```python
import json
from unittest.mock import patch, AsyncMock
from uuid import uuid4
import pytest
from src.services.resource_processor import summarize
from src.models.resource_item import ResourceType

@pytest.mark.asyncio
async def test_summarize():
    fake = {"summary":"豆包二面偏业务","signals":[{"type":"question_pattern","content":"必问北极星指标"}],"companies":["字节"]}
    with patch("src.services.resource_processor._llm.acomplete", AsyncMock(return_value=json.dumps(fake))):
        out = await summarize("面经原文...", ResourceType.INTERVIEW_RECALL, uuid4())
    assert "北极星" in out["signals"][0]["content"]
    assert out["companies"] == ["字节"]
```

Run: PASS

- [ ] **Step 4：提交**

```bash
git add apps/api && git commit -m "feat(api): resource summarizer + signal extractor (abab6.5s-chat)"
```

---

## Task 3: API — Resource CRUD + AI 处理 + Collection CRUD + 关联

**Files:**
- Create: `apps/api/src/routers/resource.py`
- Create: `apps/api/src/schemas/resource.py`
- Modify: `apps/api/src/main.py`
- Create: `apps/api/tests/test_resource_api.py`

**Interfaces:**
- Produces:
  - `POST /api/v1/resources` body `{type, title, content_text, source_url?, tags?}` → 落库 + 异步触发 summarize（v1 同步等待，时间在 1-2s 内）
  - `GET /api/v1/resources?type=&collection_id=&page=` → 列表
  - `GET /api/v1/resources/{id}` → 详情
  - `PATCH /api/v1/resources/{id}` → 更新（content_text 变化触发重摘要）
  - `DELETE /api/v1/resources/{id}` → 删除
  - `POST /api/v1/resource-collections` body `{name, description?}` → 创建
  - `GET /api/v1/resource-collections` → 列表
  - `PATCH /api/v1/resource-collections/{id}` / `DELETE`
  - `POST /api/v1/resource-collections/{id}/items/{resource_id}` → 加入合集
  - `DELETE /api/v1/resource-collections/{id}/items/{resource_id}` → 移出
  - `POST /api/v1/applications/{app_id}/resources/{resource_id}` → 关联资源到机会
  - `DELETE /api/v1/applications/{app_id}/resources/{resource_id}` → 解除关联
  - `GET /api/v1/applications/{app_id}/resources` → 该机会关联的资源列表
  - 容量门：≤100 资源、≤5 合集

- [ ] **Step 1：schema**

`apps/api/src/schemas/resource.py`：
```python
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from src.models.resource_item import ResourceType

class CreateResourceIn(BaseModel):
    type: ResourceType = ResourceType.OTHER
    title: str
    content_text: str = ""
    source_url: str | None = None
    tags: list[str] = []

class UpdateResourceIn(BaseModel):
    type: ResourceType | None = None
    title: str | None = None
    content_text: str | None = None
    source_url: str | None = None
    tags: list[str] | None = None

class ResourceOut(BaseModel):
    id: UUID
    type: ResourceType
    title: str
    content_text: str
    source_url: str | None
    tags: list[str]
    ai_summary: str
    ai_extracted_signals: list[dict]
    linked_company_names: list[str]
    created_at: datetime

class ResourceList(BaseModel):
    items: list[ResourceOut]
    total: int

class CollectionIn(BaseModel):
    name: str
    description: str = ""

class CollectionOut(BaseModel):
    id: UUID
    name: str
    description: str
    created_at: datetime
    item_count: int
```

- [ ] **Step 2：router**

`apps/api/src/routers/resource.py`：
```python
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.core.db import get_db
from src.core.deps import current_user
from src.models import User
from src.models.resource_item import ResourceItem, ResourceType
from src.models.resource_collection import ResourceCollection
from src.models.resource_collection_link import ResourceCollectionLink
from src.models.application_resource_link import ApplicationResourceLink
from src.schemas.resource import (
    CreateResourceIn, UpdateResourceIn, ResourceOut, ResourceList,
    CollectionIn, CollectionOut,
)
from src.services.resource_processor import summarize

router = APIRouter(prefix="/api/v1", tags=["resources"])

MAX_RESOURCES = 100
MAX_COLLECTIONS = 5

def _ser_r(r: ResourceItem) -> ResourceOut:
    return ResourceOut(
        id=r.id, type=r.type, title=r.title, content_text=r.content_text,
        source_url=r.source_url, tags=r.tags, ai_summary=r.ai_summary,
        ai_extracted_signals=r.ai_extracted_signals,
        linked_company_names=r.linked_company_names, created_at=r.created_at,
    )

# ============ Resources ============

@router.post("/resources", response_model=ResourceOut, status_code=201)
async def create_resource(body: CreateResourceIn, user: User = Depends(current_user), db: Session = Depends(get_db)) -> ResourceOut:
    cnt = db.query(func.count(ResourceItem.id)).filter(ResourceItem.user_id == user.id).scalar() or 0
    if cnt >= MAX_RESOURCES:
        raise HTTPException(409, {"code": "capacity_resources", "message": f"资源数已达 {MAX_RESOURCES}"})
    r = ResourceItem(user_id=user.id, **body.model_dump())
    db.add(r); db.flush()
    if r.content_text:
        try:
            ai = await summarize(r.content_text, r.type, user.id)
            r.ai_summary = ai.get("summary", "")
            r.ai_extracted_signals = ai.get("signals", [])
            r.linked_company_names = ai.get("companies", [])
        except Exception:
            pass
    db.commit(); db.refresh(r)
    return _ser_r(r)

@router.get("/resources", response_model=ResourceList)
def list_resources(
    type: ResourceType | None = None,
    collection_id: UUID | None = None,
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100),
    user: User = Depends(current_user), db: Session = Depends(get_db),
) -> ResourceList:
    q = db.query(ResourceItem).filter(ResourceItem.user_id == user.id)
    if type: q = q.filter(ResourceItem.type == type)
    if collection_id:
        q = q.join(ResourceCollectionLink, ResourceCollectionLink.resource_id == ResourceItem.id) \
             .filter(ResourceCollectionLink.collection_id == collection_id)
    total = q.count()
    rows = q.order_by(ResourceItem.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    return ResourceList(items=[_ser_r(r) for r in rows], total=total)

@router.get("/resources/{rid}", response_model=ResourceOut)
def get_resource(rid: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> ResourceOut:
    r = db.query(ResourceItem).filter(ResourceItem.id == rid, ResourceItem.user_id == user.id).first()
    if not r: raise HTTPException(404)
    return _ser_r(r)

@router.patch("/resources/{rid}", response_model=ResourceOut)
async def update_resource(rid: UUID, body: UpdateResourceIn, user: User = Depends(current_user), db: Session = Depends(get_db)) -> ResourceOut:
    r = db.query(ResourceItem).filter(ResourceItem.id == rid, ResourceItem.user_id == user.id).first()
    if not r: raise HTTPException(404)
    text_changed = body.content_text is not None and body.content_text != r.content_text
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(r, k, v)
    if text_changed and r.content_text:
        try:
            ai = await summarize(r.content_text, r.type, user.id)
            r.ai_summary = ai.get("summary", "")
            r.ai_extracted_signals = ai.get("signals", [])
            r.linked_company_names = ai.get("companies", [])
        except Exception:
            pass
    db.commit(); db.refresh(r)
    return _ser_r(r)

@router.delete("/resources/{rid}", status_code=204)
def delete_resource(rid: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> None:
    r = db.query(ResourceItem).filter(ResourceItem.id == rid, ResourceItem.user_id == user.id).first()
    if not r: raise HTTPException(404)
    db.delete(r); db.commit()

# ============ Collections ============

@router.post("/resource-collections", response_model=CollectionOut, status_code=201)
def create_collection(body: CollectionIn, user: User = Depends(current_user), db: Session = Depends(get_db)) -> CollectionOut:
    cnt = db.query(func.count(ResourceCollection.id)).filter(ResourceCollection.user_id == user.id).scalar() or 0
    if cnt >= MAX_COLLECTIONS:
        raise HTTPException(409, {"code": "capacity_collections", "message": f"合集数已达 {MAX_COLLECTIONS}"})
    c = ResourceCollection(user_id=user.id, **body.model_dump())
    db.add(c); db.commit(); db.refresh(c)
    return CollectionOut(id=c.id, name=c.name, description=c.description, created_at=c.created_at, item_count=0)

@router.get("/resource-collections", response_model=list[CollectionOut])
def list_collections(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[CollectionOut]:
    cs = db.query(ResourceCollection).filter(ResourceCollection.user_id == user.id).all()
    out = []
    for c in cs:
        n = db.query(func.count(ResourceCollectionLink.resource_id)).filter(ResourceCollectionLink.collection_id == c.id).scalar() or 0
        out.append(CollectionOut(id=c.id, name=c.name, description=c.description, created_at=c.created_at, item_count=n))
    return out

@router.patch("/resource-collections/{cid}", response_model=CollectionOut)
def update_collection(cid: UUID, body: CollectionIn, user: User = Depends(current_user), db: Session = Depends(get_db)) -> CollectionOut:
    c = db.query(ResourceCollection).filter(ResourceCollection.id == cid, ResourceCollection.user_id == user.id).first()
    if not c: raise HTTPException(404)
    c.name = body.name; c.description = body.description
    db.commit(); db.refresh(c)
    n = db.query(func.count(ResourceCollectionLink.resource_id)).filter(ResourceCollectionLink.collection_id == c.id).scalar() or 0
    return CollectionOut(id=c.id, name=c.name, description=c.description, created_at=c.created_at, item_count=n)

@router.delete("/resource-collections/{cid}", status_code=204)
def delete_collection(cid: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> None:
    c = db.query(ResourceCollection).filter(ResourceCollection.id == cid, ResourceCollection.user_id == user.id).first()
    if not c: raise HTTPException(404)
    db.query(ResourceCollectionLink).filter(ResourceCollectionLink.collection_id == cid).delete()
    db.delete(c); db.commit()

@router.post("/resource-collections/{cid}/items/{rid}", status_code=201)
def add_to_collection(cid: UUID, rid: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    db.merge(ResourceCollectionLink(collection_id=cid, resource_id=rid))
    db.commit(); return {"ok": True}

@router.delete("/resource-collections/{cid}/items/{rid}", status_code=204)
def remove_from_collection(cid: UUID, rid: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> None:
    db.query(ResourceCollectionLink).filter(
        ResourceCollectionLink.collection_id == cid, ResourceCollectionLink.resource_id == rid
    ).delete()
    db.commit()

# ============ Application 关联 ============

@router.post("/applications/{app_id}/resources/{rid}", status_code=201)
def link_resource_to_app(app_id: UUID, rid: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    db.merge(ApplicationResourceLink(application_id=app_id, resource_item_id=rid))
    db.commit(); return {"ok": True}

@router.delete("/applications/{app_id}/resources/{rid}", status_code=204)
def unlink_resource(app_id: UUID, rid: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> None:
    db.query(ApplicationResourceLink).filter(
        ApplicationResourceLink.application_id == app_id,
        ApplicationResourceLink.resource_item_id == rid,
    ).delete()
    db.commit()

@router.get("/applications/{app_id}/resources", response_model=list[ResourceOut])
def list_app_resources(app_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[ResourceOut]:
    rows = db.query(ResourceItem).join(
        ApplicationResourceLink, ApplicationResourceLink.resource_item_id == ResourceItem.id
    ).filter(
        ApplicationResourceLink.application_id == app_id, ResourceItem.user_id == user.id,
    ).all()
    return [_ser_r(r) for r in rows]
```

Modify main.py 加 include。

- [ ] **Step 3：测试**

`apps/api/tests/test_resource_api.py`：
```python
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from src.main import app
from src.core.security import issue_session_token
from src.core.db import SessionLocal
from src.models import User

def _login():
    db = SessionLocal()
    u = User(preferences={}); db.add(u); db.commit(); db.refresh(u)
    c = TestClient(app); c.cookies.set("jc_session", issue_session_token(u.id))
    return c

def test_create_resource_with_ai_summary():
    fake = {"summary":"摘要","signals":[],"companies":["字节"]}
    with patch("src.routers.resource.summarize", AsyncMock(return_value=fake)):
        c = _login()
        r = c.post("/api/v1/resources", json={"type":"interview_recall","title":"豆包二面","content_text":"问了北极星"})
    assert r.status_code == 201
    assert r.json()["ai_summary"] == "摘要"
    assert r.json()["linked_company_names"] == ["字节"]

def test_create_collection_and_link():
    c = _login()
    cr = c.post("/api/v1/resource-collections", json={"name":"字节面试"})
    cid = cr.json()["id"]
    with patch("src.routers.resource.summarize", AsyncMock(return_value={"summary":"","signals":[],"companies":[]})):
        rr = c.post("/api/v1/resources", json={"type":"other","title":"t","content_text":"x"})
    rid = rr.json()["id"]
    lk = c.post(f"/api/v1/resource-collections/{cid}/items/{rid}")
    assert lk.status_code == 201
    lst = c.get(f"/api/v1/resources?collection_id={cid}")
    assert lst.json()["total"] == 1
```

Run: PASS

- [ ] **Step 4：提交**

```bash
cd ../.. && git add apps/api && git commit -m "feat(api): resource + collection CRUD + AI summarize + application linking"
```

---

## Task 4: Web — Resource Hooks

**Files:**
- Create: `apps/web/src/hooks/useResources.ts`

**Interfaces:**
- Produces：CRUD + 合集 CRUD + 机会关联，全部用 TanStack Query

- [ ] **Step 1**

```typescript
'use client'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'

export function useResources(params: { type?: string; collection_id?: string } = {}) {
  const qs = new URLSearchParams(Object.entries(params).filter(([,v]) => !!v) as any).toString()
  return useQuery({ queryKey: ['resources', params], queryFn: () => api<{ items: any[]; total: number }>(`/api/v1/resources${qs ? '?' + qs : ''}`) })
}

export function useCreateResource() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { type: string; title: string; content_text?: string; source_url?: string; tags?: string[] }) =>
      api('/api/v1/resources', { method: 'POST', body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['resources'] }),
  })
}

export function useUpdateResource(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: any) => api(`/api/v1/resources/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['resources'] }),
  })
}

export function useDeleteResource() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api(`/api/v1/resources/${id}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['resources'] }),
  })
}

export function useCollections() {
  return useQuery({ queryKey: ['collections'], queryFn: () => api<any[]>('/api/v1/resource-collections') })
}

export function useCreateCollection() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { name: string; description?: string }) => api('/api/v1/resource-collections', { method: 'POST', body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['collections'] }),
  })
}

export function useDeleteCollection() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api(`/api/v1/resource-collections/${id}`, { method: 'DELETE' }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['collections'] }); qc.invalidateQueries({ queryKey: ['resources'] }) },
  })
}

export function useLinkToCollection() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (vars: { cid: string; rid: string }) => api(`/api/v1/resource-collections/${vars.cid}/items/${vars.rid}`, { method: 'POST' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['resources'] }),
  })
}

export function useApplicationResources(appId: string) {
  return useQuery({ queryKey: ['app-resources', appId], queryFn: () => api<any[]>(`/api/v1/applications/${appId}/resources`), enabled: !!appId })
}

export function useLinkResourceToApp(appId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (rid: string) => api(`/api/v1/applications/${appId}/resources/${rid}`, { method: 'POST' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['app-resources', appId] }),
  })
}
```

- [ ] **Step 2：提交**

```bash
git add apps/web && git commit -m "feat(web): resource + collection + application-link hooks"
```

---

## Task 5: Web — Resource Library 主页（一级入口）

**Files:**
- Modify: `apps/web/src/app/[locale]/(app)/resources/page.tsx`
- Create: `apps/web/src/components/resources/ResourceList.tsx`
- Create: `apps/web/src/components/resources/ResourceCard.tsx`
- Create: `apps/web/src/components/resources/NewResourceDialog.tsx`
- Create: `apps/web/src/components/resources/CollectionSidebar.tsx`
- Modify: `apps/web/messages/{zh,en}.json`

**Interfaces:**
- Produces:
  - 左：合集 sidebar（含"全部"和"未分类"）+ 新建合集按钮
  - 右：当前合集/类型下的资源列表 + 新增资源
  - 每条资源卡片显示：type icon · 标题 · AI 摘要 · 标签 · 关联公司 · 信号数量

- [ ] **Step 1：翻译**

zh.json 追加：
```json
"resources": {
  "title":"我的资源库",
  "new_resource":"+ 新资源",
  "new_collection":"+ 新合集",
  "type_all":"全部类型","type_interview_recall":"面经","type_company_intel":"公司情报",
  "type_recruiter_bg":"招聘者背景","type_industry_doc":"行业资料","type_other":"其他",
  "coll_all":"全部资源","coll_unassigned":"未分类",
  "empty":"没有资源，先添加一条面经或情报",
  "fields_title":"标题","fields_content":"原文","fields_source_url":"来源链接（可选）","fields_tags":"标签（逗号分隔）",
  "save":"保存","cancel":"取消",
  "signals":"AI 信号","companies":"识别公司",
  "delete_confirm":"确定删除？"
}
```

en.json 对应。

- [ ] **Step 2：CollectionSidebar**

```typescript
'use client'
import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { useCollections, useCreateCollection, useDeleteCollection } from '@/hooks/useResources'

export function CollectionSidebar({ currentId, onPick }: { currentId: string | null; onPick: (id: string | null) => void }) {
  const t = useTranslations('resources')
  const { data: cols } = useCollections()
  const create = useCreateCollection()
  const del = useDeleteCollection()
  const [newName, setNewName] = useState('')

  return (
    <aside className="w-56 border-r pr-3 space-y-2 text-sm">
      <button onClick={() => onPick(null)} className={`w-full text-left px-2 py-1 rounded ${!currentId ? 'bg-black text-white' : ''}`}>
        📚 {t('coll_all')}
      </button>
      {(cols ?? []).map((c: any) => (
        <div key={c.id} className="flex items-center justify-between group">
          <button onClick={() => onPick(c.id)} className={`flex-1 text-left px-2 py-1 rounded ${currentId === c.id ? 'bg-black text-white' : ''}`}>
            🗂 {c.name} <span className="text-xs opacity-60">({c.item_count})</span>
          </button>
          <button onClick={() => confirm(t('delete_confirm')) && del.mutate(c.id)} className="opacity-0 group-hover:opacity-100 text-red-600">✕</button>
        </div>
      ))}
      <form onSubmit={(e) => { e.preventDefault(); if (!newName) return; create.mutate({ name: newName }); setNewName('') }}
            className="pt-3 border-t">
        <input value={newName} onChange={(e) => setNewName(e.target.value)} placeholder={t('new_collection')}
               className="w-full border rounded px-2 py-1 text-sm" />
      </form>
    </aside>
  )
}
```

- [ ] **Step 3：ResourceCard**

```typescript
'use client'
import { useTranslations } from 'next-intl'
import { useDeleteResource } from '@/hooks/useResources'

const ICON: Record<string, string> = {
  interview_recall: '🎤', company_intel: '🏢', recruiter_bg: '👤', industry_doc: '📰', other: '📌'
}

export function ResourceCard({ r }: { r: any }) {
  const t = useTranslations('resources')
  const del = useDeleteResource()
  return (
    <div className="border rounded p-3 space-y-1">
      <div className="flex items-center justify-between">
        <div className="font-semibold">{ICON[r.type] ?? '📌'} {r.title}</div>
        <button onClick={() => confirm(t('delete_confirm')) && del.mutate(r.id)} className="text-red-600 text-sm">✕</button>
      </div>
      {r.ai_summary && <p className="text-sm text-gray-700">{r.ai_summary}</p>}
      {r.linked_company_names?.length > 0 && <div className="text-xs">🏢 {r.linked_company_names.join(', ')}</div>}
      {r.ai_extracted_signals?.length > 0 && (
        <details className="text-xs">
          <summary className="cursor-pointer">{t('signals')} ({r.ai_extracted_signals.length})</summary>
          <ul className="pl-4 list-disc">{r.ai_extracted_signals.map((s: any, i: number) => <li key={i}><b>{s.type}：</b>{s.content}</li>)}</ul>
        </details>
      )}
      {r.tags?.length > 0 && <div className="flex gap-1 flex-wrap">{r.tags.map((g: string) => <span key={g} className="bg-gray-100 text-xs px-2 py-0.5 rounded">{g}</span>)}</div>}
    </div>
  )
}
```

- [ ] **Step 4：NewResourceDialog**

```typescript
'use client'
import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { useCreateResource } from '@/hooks/useResources'

const TYPES = ['interview_recall','company_intel','recruiter_bg','industry_doc','other'] as const

export function NewResourceDialog({ onClose }: { onClose: () => void }) {
  const t = useTranslations('resources')
  const create = useCreateResource()
  const [type, setType] = useState<typeof TYPES[number]>('interview_recall')
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [url, setUrl] = useState('')
  const [tags, setTags] = useState('')
  async function save() {
    await create.mutateAsync({
      type, title, content_text: content, source_url: url || undefined,
      tags: tags ? tags.split(',').map(s => s.trim()).filter(Boolean) : [],
    })
    onClose()
  }
  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center" onClick={onClose}>
      <div className="bg-white rounded p-6 w-[720px] max-w-[95%] space-y-3" onClick={(e) => e.stopPropagation()}>
        <h3 className="font-bold">{t('new_resource')}</h3>
        <div className="flex gap-2 text-sm">
          {TYPES.map((tp) => (
            <button key={tp} onClick={() => setType(tp)}
                    className={`px-2 py-1 border rounded ${tp === type ? 'bg-black text-white' : ''}`}>
              {t(`type_${tp}` as any)}
            </button>
          ))}
        </div>
        <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder={t('fields_title')} className="w-full border rounded px-3 py-2" />
        <textarea value={content} onChange={(e) => setContent(e.target.value)} placeholder={t('fields_content')} rows={8} className="w-full border rounded px-3 py-2" />
        <input value={url} onChange={(e) => setUrl(e.target.value)} placeholder={t('fields_source_url')} className="w-full border rounded px-3 py-2 text-sm" />
        <input value={tags} onChange={(e) => setTags(e.target.value)} placeholder={t('fields_tags')} className="w-full border rounded px-3 py-2 text-sm" />
        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="px-3 py-2">{t('cancel')}</button>
          <button onClick={save} disabled={create.isPending || !title} className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50">
            {create.isPending ? '…' : t('save')}
          </button>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 5：ResourceList + page**

```typescript
'use client'
import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { useResources } from '@/hooks/useResources'
import { CollectionSidebar } from '@/components/resources/CollectionSidebar'
import { ResourceCard } from '@/components/resources/ResourceCard'
import { NewResourceDialog } from '@/components/resources/NewResourceDialog'

const TYPE_FILTERS = [
  { v: undefined, label: 'type_all' },
  { v: 'interview_recall', label: 'type_interview_recall' },
  { v: 'company_intel', label: 'type_company_intel' },
  { v: 'recruiter_bg', label: 'type_recruiter_bg' },
  { v: 'industry_doc', label: 'type_industry_doc' },
  { v: 'other', label: 'type_other' },
] as const

export default function ResourcesPage() {
  const t = useTranslations('resources')
  const [cid, setCid] = useState<string | null>(null)
  const [type, setType] = useState<string | undefined>(undefined)
  const [open, setOpen] = useState(false)
  const { data } = useResources({ type, collection_id: cid ?? undefined })

  return (
    <div className="flex gap-6">
      <CollectionSidebar currentId={cid} onPick={setCid} />
      <div className="flex-1 space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">{t('title')}</h1>
          <button onClick={() => setOpen(true)} className="bg-black text-white px-4 py-2 rounded">{t('new_resource')}</button>
        </div>
        <div className="flex gap-2 flex-wrap">
          {TYPE_FILTERS.map((f) => (
            <button key={f.label} onClick={() => setType(f.v)}
                    className={`px-3 py-1 text-sm border rounded ${type === f.v ? 'bg-black text-white' : ''}`}>
              {t(f.label as any)}
            </button>
          ))}
        </div>
        <div className="space-y-3">
          {(data?.items ?? []).map((r: any) => <ResourceCard key={r.id} r={r} />)}
          {data?.items?.length === 0 && <p className="text-gray-500">{t('empty')}</p>}
        </div>
      </div>
      {open && <NewResourceDialog onClose={() => setOpen(false)} />}
    </div>
  )
}
```

- [ ] **Step 6：提交**

```bash
git add apps/web && git commit -m "feat(web): resource library page with collection sidebar + type filter + dialog"
```

---

## Task 6: Web — 简历定制页面侧栏关联资源

**Files:**
- Modify: `apps/web/src/components/resume/JDInsightPanel.tsx`（追加"已关联资源"区）
- Create: `apps/web/src/components/resume/LinkedResourcesPanel.tsx`

**Interfaces:**
- Produces:
  - 在简历定制页 JDInsightPanel 下方追加"已关联资源"列表
  - "+ 关联资源"按钮 → 弹窗从已有 ResourceLibrary 选择关联

- [ ] **Step 1：LinkedResourcesPanel**

```typescript
'use client'
import { useState } from 'react'
import { useApplicationResources, useLinkResourceToApp, useResources } from '@/hooks/useResources'

export function LinkedResourcesPanel({ appId }: { appId: string }) {
  const { data: linked } = useApplicationResources(appId)
  const [open, setOpen] = useState(false)
  return (
    <div className="border rounded p-3 mt-3 text-sm">
      <div className="flex items-center justify-between">
        <strong>已关联资源</strong>
        <button onClick={() => setOpen(true)} className="text-xs border rounded px-2 py-0.5">+ 关联</button>
      </div>
      <ul className="mt-2 space-y-1">
        {(linked ?? []).map((r: any) => <li key={r.id}>📌 {r.title}{r.ai_summary && <span className="text-gray-500"> — {r.ai_summary.slice(0, 30)}…</span>}</li>)}
        {linked?.length === 0 && <li className="text-gray-400">暂无</li>}
      </ul>
      {open && <PickerDialog appId={appId} onClose={() => setOpen(false)} />}
    </div>
  )
}

function PickerDialog({ appId, onClose }: { appId: string; onClose: () => void }) {
  const { data } = useResources({})
  const link = useLinkResourceToApp(appId)
  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center" onClick={onClose}>
      <div className="bg-white rounded p-4 w-96 max-h-[70vh] overflow-auto" onClick={(e) => e.stopPropagation()}>
        <h4 className="font-bold mb-2">从资源库选择</h4>
        <ul className="space-y-1 text-sm">
          {(data?.items ?? []).map((r: any) => (
            <li key={r.id}>
              <button onClick={() => { link.mutate(r.id); onClose() }} className="text-left w-full hover:bg-gray-50 px-2 py-1 rounded">
                📌 {r.title}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
```

- [ ] **Step 2：插入到 JDInsightPanel**

修改 `JDInsightPanel.tsx`：函数签名增加 appId，末尾追加：
```typescript
import { LinkedResourcesPanel } from './LinkedResourcesPanel'
// ...
export function JDInsightPanel({ jp, matchScore, appId }: { jp: any; matchScore: number | null; appId: string }) {
  // ... 原代码 ...
  return (
    <aside className="w-72 border-r pr-4 space-y-3 text-sm">
      {/* 原有内容 */}
      <LinkedResourcesPanel appId={appId} />
    </aside>
  )
}
```

修改 resume/page.tsx 传入 appId：`<JDInsightPanel jp={appData?.job_posting} matchScore={branch?.match_score ?? null} appId={appId} />`

- [ ] **Step 3：提交**

```bash
git add apps/web && git commit -m "feat(web): linked resources panel in resume customization sidebar"
```

---

## Task 7: PostHog + e2e

**Files:**
- Modify: `packages/shared-types/events.ts`
- Modify: `apps/web/src/hooks/useResources.ts`
- Create: `apps/web/e2e/resources.spec.ts`

**Interfaces:**
- Produces：events `RESOURCE_CREATED` `RESOURCE_DELETED` `COLLECTION_CREATED` `RESOURCE_LINKED_TO_APP`

- [ ] **Step 1**

```typescript
export const Events = {
  // ...
  RESOURCE_CREATED: 'resource_created',
  RESOURCE_DELETED: 'resource_deleted',
  COLLECTION_CREATED: 'collection_created',
  RESOURCE_LINKED_TO_APP: 'resource_linked_to_app',
} as const
```

各 hook onSuccess track。

- [ ] **Step 2：e2e**

```typescript
import { test, expect } from '@playwright/test'

test('resources page renders sidebar + filters', async ({ page }) => {
  await page.goto('/zh/resources')
  await expect(page.getByRole('heading', { name: '我的资源库' })).toBeVisible()
  await expect(page.getByRole('button', { name: '+ 新资源' })).toBeVisible()
})
```

- [ ] **Step 3：提交**

```bash
git add packages apps && git commit -m "feat: posthog events + e2e for resources"
```

---

## Plan 4 完成判定

```bash
pnpm --filter api test && pnpm --filter web typecheck && pnpm --filter web e2e
# 手动：/zh/resources → 新建合集"字节面试" → 新建资源（粘面经） → 看到 AI 摘要 + 信号 → 资源加入合集
# 进入某机会的简历定制 → 关联该资源 → 在简历定制侧栏看到"已关联资源"
```

下一站 → Plan 5 (Investment 投递记录)
