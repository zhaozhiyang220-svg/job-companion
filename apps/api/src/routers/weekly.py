from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.core.deps import current_user
from src.models import User
from src.models.weekly_digest import WeeklyDigest
from src.schemas.weekly import WeeklyHistoryItem, WeeklyOut
from src.services.weekly_digester import get_or_create

router = APIRouter(prefix="/api/v1/weekly", tags=["weekly"])


def _parse(week_of: str | None) -> date | None:
    return date.fromisoformat(week_of) if week_of else None


def _out(d: WeeklyDigest) -> WeeklyOut:
    return WeeklyOut(
        id=d.id,
        week_of=d.week_of,
        stats=d.stats,
        ai_observation_text=d.ai_observation_text,
        suggested_actions=d.suggested_actions,
        generated_at=d.generated_at,
    )


@router.get("", response_model=WeeklyOut)
async def get_weekly(
    week_of: str | None = None,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> WeeklyOut:
    d = await get_or_create(db, user.id, _parse(week_of), force_refresh=False)
    return _out(d)


@router.post("/refresh", response_model=WeeklyOut)
async def refresh_weekly(
    week_of: str | None = None,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> WeeklyOut:
    d = await get_or_create(db, user.id, _parse(week_of), force_refresh=True)
    return _out(d)


@router.get("/history", response_model=list[WeeklyHistoryItem])
def history(
    weeks: int = Query(8, ge=1, le=52),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> list[WeeklyHistoryItem]:
    rows = (
        db.query(WeeklyDigest)
        .filter(WeeklyDigest.user_id == user.id)
        .order_by(WeeklyDigest.week_of.desc())
        .limit(weeks)
        .all()
    )
    return [WeeklyHistoryItem(week_of=r.week_of, stats=r.stats) for r in rows]
