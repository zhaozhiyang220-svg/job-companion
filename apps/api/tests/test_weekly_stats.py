from datetime import datetime

from sqlalchemy.orm import Session

from src.models import Application, JobPosting, User
from src.services.time_helpers import BJT, monday_of
from src.services.weekly_stats import compute_stats


def test_stats_counts_new_apps(db: Session) -> None:
    u = User(preferences={})
    db.add(u)
    db.flush()
    a = Application(user_id=u.id)
    a.job_posting = JobPosting(raw_text="x")
    db.add(a)
    db.commit()
    m = monday_of(datetime.now(BJT))
    s = compute_stats(db, u.id, m)
    assert s["new_applications"] >= 1
    assert s["total_active_applications"] >= 1
