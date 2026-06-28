import contextlib
from datetime import date, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from src.models import Application
from src.models.weekly_digest import WeeklyDigest
from src.services.time_helpers import BJT, monday_of, week_range
from src.services.weekly_observer import generate_observation
from src.services.weekly_stats import compute_stats


async def get_or_create(
    db: Session,
    user_id: UUID,
    monday: date | None = None,
    force_refresh: bool = False,
) -> WeeklyDigest:
    m = monday or monday_of(datetime.now(BJT))
    existing = (
        db.query(WeeklyDigest)
        .filter(WeeklyDigest.user_id == user_id, WeeklyDigest.week_of == m)
        .first()
    )
    if existing and not force_refresh:
        return existing

    stats = compute_stats(db, user_id, m)
    start, end = week_range(m)
    new_jds: list[dict[str, object]] = []
    rows = (
        db.query(Application)
        .filter(
            Application.user_id == user_id,
            Application.created_at >= start,
            Application.created_at <= end,
        )
        .all()
    )
    for a in rows:
        jp = a.job_posting
        if not jp:
            continue
        hard = jp.requirements_parsed.get("hard", []) if jp.requirements_parsed else []
        new_jds.append(
            {
                "company": jp.company_name,
                "title": jp.job_title,
                "hard_skills_top": hard[:3] if isinstance(hard, list) else [],
            }
        )

    text = (
        f"本周共 {stats['new_applications']} 个新机会、{stats['new_branches']} 个简历版本。"
    )
    actions: list[dict[str, object]] = []
    with contextlib.suppress(Exception):
        ai_out = await generate_observation(stats, new_jds, user_id)
        text = str(ai_out.get("text", "")) or text
        raw_actions = ai_out.get("suggested_actions", [])
        actions = raw_actions if isinstance(raw_actions, list) else []

    if existing:
        existing.stats = dict(stats)
        existing.ai_observation_text = text
        existing.suggested_actions = actions
    else:
        existing = WeeklyDigest(
            user_id=user_id,
            week_of=m,
            stats=dict(stats),
            ai_observation_text=text,
            suggested_actions=actions,
        )
        db.add(existing)
    db.commit()
    db.refresh(existing)
    return existing
