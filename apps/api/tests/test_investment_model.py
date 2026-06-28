from datetime import UTC, datetime

from sqlalchemy.orm import Session

from src.models import Application, Investment, InvestmentActionType, JobPosting, User


def test_create_investment(db: Session) -> None:
    u = User(preferences={})
    db.add(u)
    db.flush()
    a = Application(user_id=u.id)
    a.job_posting = JobPosting(raw_text="x")
    db.add(a)
    db.flush()
    iv = Investment(
        application_id=a.id,
        action_type=InvestmentActionType.SUBMITTED,
        action_at=datetime.now(UTC),
        channel="Boss直聘",
        notes="投递成功",
    )
    db.add(iv)
    db.flush()
    assert iv.action_type == InvestmentActionType.SUBMITTED
