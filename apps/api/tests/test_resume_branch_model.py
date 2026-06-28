from sqlalchemy.orm import Session

from src.models import Application, JobPosting, ResumeBranch, User


def test_create_branch(db: Session) -> None:
    u = User(preferences={})
    db.add(u)
    db.flush()
    a = Application(user_id=u.id)
    a.job_posting = JobPosting(raw_text="x")
    db.add(a)
    db.flush()
    b = ResumeBranch(
        application_id=a.id,
        version_label="v1",
        patch=[{"type": "hide", "card_id": "x"}],
        ai_reasoning=[{"op_index": 0, "reason": "无关岗位"}],
        match_score=72,
        language="zh",
    )
    db.add(b)
    db.flush()
    assert b.match_score == 72
    assert b.patch[0]["type"] == "hide"
