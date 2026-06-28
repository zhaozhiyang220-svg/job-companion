from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Date, cast, func
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.core.internal_auth import require_internal_password
from src.models import User
from src.models.ai_call_log import AICallLog
from src.models.coach_inquiry import CoachInquiry
from src.schemas.internal import DailyRow, DashboardSummary, TimeSeries
from src.services.time_helpers import BJT, monday_of, week_range

router = APIRouter(
    prefix="/internal/dashboard",
    tags=["internal"],
    dependencies=[Depends(require_internal_password)],
)


@router.get("/summary", response_model=DashboardSummary)
def summary(db: Session = Depends(get_db)) -> DashboardSummary:
    now = datetime.now(UTC)
    today_start = datetime.combine(now.date(), datetime.min.time(), tzinfo=UTC)
    last_30 = now - timedelta(days=30)
    last_1 = now - timedelta(days=1)

    mau = (
        db.query(func.count(func.distinct(User.id)))
        .filter(User.last_active_at >= last_30)
        .scalar()
        or 0
    )
    dau = (
        db.query(func.count(func.distinct(User.id)))
        .filter(User.last_active_at >= last_1)
        .scalar()
        or 0
    )
    total = db.query(func.count(User.id)).scalar() or 0
    calls_today = (
        db.query(func.count(AICallLog.id))
        .filter(AICallLog.created_at >= today_start)
        .scalar()
        or 0
    )
    cost_today = float(
        db.query(func.coalesce(func.sum(AICallLog.cost_usd), 0))
        .filter(AICallLog.created_at >= today_start)
        .scalar()
        or 0
    )
    calls_30 = (
        db.query(func.count(AICallLog.id)).filter(AICallLog.created_at >= last_30).scalar()
        or 0
    )
    cost_30 = float(
        db.query(func.coalesce(func.sum(AICallLog.cost_usd), 0))
        .filter(AICallLog.created_at >= last_30)
        .scalar()
        or 0
    )
    m = monday_of(datetime.now(BJT))
    ws, we = week_range(m)
    coach_week = (
        db.query(func.count(CoachInquiry.id))
        .filter(CoachInquiry.created_at >= ws, CoachInquiry.created_at <= we)
        .scalar()
        or 0
    )
    return DashboardSummary(
        dau=dau,
        mau=mau,
        total_users=total,
        ai_calls_today=calls_today,
        ai_cost_today_usd=cost_today,
        ai_calls_30d=calls_30,
        ai_cost_30d_usd=cost_30,
        coach_inquiries_week=coach_week,
    )


@router.get("/timeseries", response_model=TimeSeries)
def timeseries(
    days: int = Query(30, ge=1, le=180), db: Session = Depends(get_db)
) -> TimeSeries:
    since = datetime.now(UTC) - timedelta(days=days)
    rows = (
        db.query(
            cast(AICallLog.created_at, Date).label("d"),
            func.count(AICallLog.id).label("n"),
            func.coalesce(func.sum(AICallLog.cost_usd), 0).label("c"),
        )
        .filter(AICallLog.created_at >= since)
        .group_by("d")
        .all()
    )
    by_d = {r.d: (r.n, float(r.c)) for r in rows}

    daily: list[DailyRow] = []
    for i in range(days):
        d = (datetime.now(UTC) - timedelta(days=days - 1 - i)).date()
        ds = datetime.combine(d, datetime.min.time(), tzinfo=UTC)
        de = ds + timedelta(days=1)
        dau = (
            db.query(func.count(func.distinct(User.id)))
            .filter(User.last_active_at >= ds, User.last_active_at < de)
            .scalar()
            or 0
        )
        n, c = by_d.get(d, (0, 0.0))
        daily.append(DailyRow(date=d, dau=dau, ai_calls=n, ai_cost=c))
    return TimeSeries(daily=daily)
