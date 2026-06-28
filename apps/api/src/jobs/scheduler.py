import contextlib
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.core.db import SessionLocal
from src.models import User
from src.services.time_helpers import BJT, monday_of
from src.services.weekly_digester import get_or_create

scheduler = AsyncIOScheduler(timezone=BJT)


async def regenerate_all_users_prev_week() -> None:
    """周一 00:30 BJT 触发：为所有 user 重算"上周"digest。"""
    prev_monday = monday_of(datetime.now(BJT)) - timedelta(days=7)
    db = SessionLocal()
    try:
        ids = [r[0] for r in db.query(User.id).all()]
        for uid in ids:
            with contextlib.suppress(Exception):
                await get_or_create(db, uid, prev_monday, force_refresh=True)
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
