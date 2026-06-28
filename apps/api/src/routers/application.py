from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from src.core.db import get_db
from src.core.deps import current_user
from src.models import Application, ApplicationStatus, JobPosting, User
from src.schemas.application import (
    ApplicationList,
    ApplicationListItem,
    ApplicationOut,
    CreateApplicationIn,
    JobPostingOut,
    UpdateApplicationIn,
)
from src.services.jd_parser import parse_jd

router = APIRouter(prefix="/api/v1/applications", tags=["applications"])

MAX_ACTIVE = 20
MAX_PER_MONTH = 15


def _serialize(a: Application) -> ApplicationOut:
    jp = a.job_posting
    return ApplicationOut(
        id=a.id,
        status=a.status,
        priority=a.priority,
        notes=a.notes,
        created_at=a.created_at,
        last_active_at=a.last_active_at,
        job_posting=JobPostingOut(
            company_name=jp.company_name,
            job_title=jp.job_title,
            department=jp.department,
            salary_range=jp.salary_range,
            location=jp.location,
            language=jp.language,
            requirements_parsed=jp.requirements_parsed,
            hidden_preferences=jp.hidden_preferences,
            red_flags=jp.red_flags,
            raw_text=jp.raw_text,
            source_url=jp.source_url,
        ),
    )


def _check_capacity(db: Session, user: User) -> None:
    active = (
        db.query(func.count(Application.id))
        .filter(
            Application.user_id == user.id,
            Application.status != ApplicationStatus.ARCHIVED,
        )
        .scalar()
        or 0
    )
    if active >= MAX_ACTIVE:
        raise HTTPException(
            409,
            {"code": "capacity_active", "message": f"已达上限 {MAX_ACTIVE}，请归档旧机会"},
        )
    since = datetime.now(UTC) - timedelta(days=30)
    monthly = (
        db.query(func.count(Application.id))
        .filter(Application.user_id == user.id, Application.created_at >= since)
        .scalar()
        or 0
    )
    if monthly >= MAX_PER_MONTH:
        raise HTTPException(
            409,
            {
                "code": "capacity_monthly",
                "message": f"30 天内新建已达 {MAX_PER_MONTH}，建议找 Coach 帮你聚焦",
            },
        )


@router.post("", response_model=ApplicationOut, status_code=201)
async def create_application(
    body: CreateApplicationIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> ApplicationOut:
    _check_capacity(db, user)
    parsed = await parse_jd(body.raw_text, user.id)
    app = Application(user_id=user.id)
    app.job_posting = JobPosting(
        raw_text=body.raw_text,
        source_url=body.source_url,
        company_name=parsed.company_name,
        job_title=parsed.job_title,
        department=parsed.department,
        salary_range=parsed.salary_range,
        location=parsed.location,
        language=parsed.language,
        requirements_parsed=parsed.requirements.model_dump(),
        hidden_preferences=parsed.hidden_preferences,
        red_flags=parsed.red_flags,
        parsed_at=datetime.now(UTC),
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return _serialize(app)


@router.get("", response_model=ApplicationList)
def list_applications(
    status: ApplicationStatus | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> ApplicationList:
    q = db.query(Application).filter(Application.user_id == user.id)
    if status:
        q = q.filter(Application.status == status)
    total = q.count()
    rows = (
        q.options(selectinload(Application.job_posting))
        .order_by(Application.last_active_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items = [
        ApplicationListItem(
            id=a.id,
            status=a.status,
            company_name=a.job_posting.company_name,
            job_title=a.job_posting.job_title,
            department=a.job_posting.department,
            salary_range=a.job_posting.salary_range,
            last_active_at=a.last_active_at,
        )
        for a in rows
    ]
    return ApplicationList(items=items, total=total, page=page, page_size=page_size)


@router.get("/{app_id}", response_model=ApplicationOut)
def get_application(
    app_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> ApplicationOut:
    a = (
        db.query(Application)
        .filter(Application.id == app_id, Application.user_id == user.id)
        .options(selectinload(Application.job_posting))
        .first()
    )
    if not a:
        raise HTTPException(404, "not found")
    return _serialize(a)


@router.patch("/{app_id}", response_model=ApplicationOut)
def update_application(
    app_id: UUID,
    body: UpdateApplicationIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> ApplicationOut:
    a = (
        db.query(Application)
        .filter(Application.id == app_id, Application.user_id == user.id)
        .first()
    )
    if not a:
        raise HTTPException(404, "not found")
    if body.status is not None:
        a.status = body.status
    if body.priority is not None:
        a.priority = body.priority
    if body.notes is not None:
        a.notes = body.notes
    db.commit()
    db.refresh(a)
    return _serialize(a)
