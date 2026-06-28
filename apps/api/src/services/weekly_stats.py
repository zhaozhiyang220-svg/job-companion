from datetime import date
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.models import Application, ApplicationStatus, ResumeBranch
from src.services.time_helpers import week_range


def compute_stats(db: Session, user_id: UUID, monday: date) -> dict[str, int]:
    start, end = week_range(monday)
    new_apps = (
        db.query(func.count(Application.id))
        .filter(
            Application.user_id == user_id,
            Application.created_at >= start,
            Application.created_at <= end,
        )
        .scalar()
        or 0
    )

    new_branches = (
        db.query(func.count(ResumeBranch.id))
        .join(Application, Application.id == ResumeBranch.application_id)
        .filter(
            Application.user_id == user_id,
            ResumeBranch.created_at >= start,
            ResumeBranch.created_at <= end,
        )
        .scalar()
        or 0
    )

    # exports：简化为本周新建分支的导出条数总和
    rows = (
        db.query(ResumeBranch)
        .join(Application, Application.id == ResumeBranch.application_id)
        .filter(
            Application.user_id == user_id,
            ResumeBranch.created_at >= start,
            ResumeBranch.created_at <= end,
        )
        .all()
    )
    exports = sum(len(r.exported_pdf_urls or []) for r in rows)

    # coach_inquiries：CoachInquiry 表在 Plan 7 创建，届时接入
    coach_inquiries = 0

    total_active = (
        db.query(func.count(Application.id))
        .filter(
            Application.user_id == user_id,
            Application.status != ApplicationStatus.ARCHIVED,
        )
        .scalar()
        or 0
    )

    return {
        "new_applications": new_apps,
        "new_branches": new_branches,
        "exports": exports,
        "coach_inquiries": coach_inquiries,
        "total_active_applications": total_active,
    }
