import contextlib
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.core.deps import current_user
from src.models import User
from src.models.application_resource_link import ApplicationResourceLink
from src.models.resource_collection import ResourceCollection
from src.models.resource_collection_link import ResourceCollectionLink
from src.models.resource_item import ResourceItem, ResourceType
from src.schemas.resource import (
    CollectionIn,
    CollectionOut,
    CreateResourceIn,
    ResourceList,
    ResourceOut,
    UpdateResourceIn,
)
from src.services.resource_processor import summarize

router = APIRouter(prefix="/api/v1", tags=["resources"])

MAX_RESOURCES = 100
MAX_COLLECTIONS = 5


def _ser_r(r: ResourceItem) -> ResourceOut:
    return ResourceOut(
        id=r.id,
        type=r.type,
        title=r.title,
        content_text=r.content_text,
        source_url=r.source_url,
        tags=r.tags,
        ai_summary=r.ai_summary,
        ai_extracted_signals=r.ai_extracted_signals,
        linked_company_names=r.linked_company_names,
        created_at=r.created_at,
    )


async def _run_summary(r: ResourceItem, user_id: UUID) -> None:
    with contextlib.suppress(Exception):
        ai = await summarize(r.content_text, r.type, user_id)
        r.ai_summary = ai.get("summary", "")
        r.ai_extracted_signals = ai.get("signals", [])
        r.linked_company_names = ai.get("companies", [])


# ============ Resources ============


@router.post("/resources", response_model=ResourceOut, status_code=201)
async def create_resource(
    body: CreateResourceIn, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> ResourceOut:
    cnt = (
        db.query(func.count(ResourceItem.id)).filter(ResourceItem.user_id == user.id).scalar()
        or 0
    )
    if cnt >= MAX_RESOURCES:
        raise HTTPException(
            409, {"code": "capacity_resources", "message": f"资源数已达 {MAX_RESOURCES}"}
        )
    r = ResourceItem(user_id=user.id, **body.model_dump())
    db.add(r)
    db.flush()
    if r.content_text:
        await _run_summary(r, user.id)
    db.commit()
    db.refresh(r)
    return _ser_r(r)


@router.get("/resources", response_model=ResourceList)
def list_resources(
    type: ResourceType | None = None,
    collection_id: UUID | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> ResourceList:
    q = db.query(ResourceItem).filter(ResourceItem.user_id == user.id)
    if type:
        q = q.filter(ResourceItem.type == type)
    if collection_id:
        q = q.join(
            ResourceCollectionLink, ResourceCollectionLink.resource_id == ResourceItem.id
        ).filter(ResourceCollectionLink.collection_id == collection_id)
    total = q.count()
    rows = (
        q.order_by(ResourceItem.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return ResourceList(items=[_ser_r(r) for r in rows], total=total)


def _get_resource(db: Session, rid: UUID, user: User) -> ResourceItem:
    r = (
        db.query(ResourceItem)
        .filter(ResourceItem.id == rid, ResourceItem.user_id == user.id)
        .first()
    )
    if not r:
        raise HTTPException(404)
    return r


@router.get("/resources/{rid}", response_model=ResourceOut)
def get_resource(
    rid: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> ResourceOut:
    return _ser_r(_get_resource(db, rid, user))


@router.patch("/resources/{rid}", response_model=ResourceOut)
async def update_resource(
    rid: UUID,
    body: UpdateResourceIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> ResourceOut:
    r = _get_resource(db, rid, user)
    text_changed = body.content_text is not None and body.content_text != r.content_text
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(r, k, v)
    if text_changed and r.content_text:
        await _run_summary(r, user.id)
    db.commit()
    db.refresh(r)
    return _ser_r(r)


@router.delete("/resources/{rid}", status_code=204)
def delete_resource(
    rid: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> None:
    r = _get_resource(db, rid, user)
    # 先清理关联行，避免外键约束阻止删除（合集/岗位关联均指向该资源）
    db.query(ResourceCollectionLink).filter(ResourceCollectionLink.resource_id == rid).delete()
    db.query(ApplicationResourceLink).filter(
        ApplicationResourceLink.resource_item_id == rid
    ).delete()
    db.delete(r)
    db.commit()


# ============ Collections ============


def _count_items(db: Session, cid: UUID) -> int:
    return (
        db.query(func.count(ResourceCollectionLink.resource_id))
        .filter(ResourceCollectionLink.collection_id == cid)
        .scalar()
        or 0
    )


def _get_collection(db: Session, cid: UUID, user: User) -> ResourceCollection:
    c = (
        db.query(ResourceCollection)
        .filter(ResourceCollection.id == cid, ResourceCollection.user_id == user.id)
        .first()
    )
    if not c:
        raise HTTPException(404)
    return c


@router.post("/resource-collections", response_model=CollectionOut, status_code=201)
def create_collection(
    body: CollectionIn, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> CollectionOut:
    cnt = (
        db.query(func.count(ResourceCollection.id))
        .filter(ResourceCollection.user_id == user.id)
        .scalar()
        or 0
    )
    if cnt >= MAX_COLLECTIONS:
        raise HTTPException(
            409, {"code": "capacity_collections", "message": f"合集数已达 {MAX_COLLECTIONS}"}
        )
    c = ResourceCollection(user_id=user.id, **body.model_dump())
    db.add(c)
    db.commit()
    db.refresh(c)
    return CollectionOut(
        id=c.id, name=c.name, description=c.description, created_at=c.created_at, item_count=0
    )


@router.get("/resource-collections", response_model=list[CollectionOut])
def list_collections(
    user: User = Depends(current_user), db: Session = Depends(get_db)
) -> list[CollectionOut]:
    cs = db.query(ResourceCollection).filter(ResourceCollection.user_id == user.id).all()
    return [
        CollectionOut(
            id=c.id,
            name=c.name,
            description=c.description,
            created_at=c.created_at,
            item_count=_count_items(db, c.id),
        )
        for c in cs
    ]


@router.patch("/resource-collections/{cid}", response_model=CollectionOut)
def update_collection(
    cid: UUID,
    body: CollectionIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> CollectionOut:
    c = _get_collection(db, cid, user)
    c.name = body.name
    c.description = body.description
    db.commit()
    db.refresh(c)
    return CollectionOut(
        id=c.id,
        name=c.name,
        description=c.description,
        created_at=c.created_at,
        item_count=_count_items(db, c.id),
    )


@router.delete("/resource-collections/{cid}", status_code=204)
def delete_collection(
    cid: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> None:
    c = _get_collection(db, cid, user)
    db.query(ResourceCollectionLink).filter(
        ResourceCollectionLink.collection_id == cid
    ).delete()
    db.delete(c)
    db.commit()


@router.post("/resource-collections/{cid}/items/{rid}", status_code=201)
def add_to_collection(
    cid: UUID, rid: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> dict[str, bool]:
    db.merge(ResourceCollectionLink(collection_id=cid, resource_id=rid))
    db.commit()
    return {"ok": True}


@router.delete("/resource-collections/{cid}/items/{rid}", status_code=204)
def remove_from_collection(
    cid: UUID, rid: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> None:
    db.query(ResourceCollectionLink).filter(
        ResourceCollectionLink.collection_id == cid,
        ResourceCollectionLink.resource_id == rid,
    ).delete()
    db.commit()


# ============ Application 关联 ============


@router.post("/applications/{app_id}/resources/{rid}", status_code=201)
def link_resource_to_app(
    app_id: UUID, rid: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> dict[str, bool]:
    db.merge(ApplicationResourceLink(application_id=app_id, resource_item_id=rid))
    db.commit()
    return {"ok": True}


@router.delete("/applications/{app_id}/resources/{rid}", status_code=204)
def unlink_resource(
    app_id: UUID, rid: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> None:
    db.query(ApplicationResourceLink).filter(
        ApplicationResourceLink.application_id == app_id,
        ApplicationResourceLink.resource_item_id == rid,
    ).delete()
    db.commit()


@router.get("/applications/{app_id}/resources", response_model=list[ResourceOut])
def list_app_resources(
    app_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> list[ResourceOut]:
    rows = (
        db.query(ResourceItem)
        .join(
            ApplicationResourceLink,
            ApplicationResourceLink.resource_item_id == ResourceItem.id,
        )
        .filter(
            ApplicationResourceLink.application_id == app_id,
            ResourceItem.user_id == user.id,
        )
        .all()
    )
    return [_ser_r(r) for r in rows]
