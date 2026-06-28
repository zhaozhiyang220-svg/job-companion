from sqlalchemy.orm import Session

from src.models import Application, ApplicationStatus, JobPosting, User


def test_application_with_job_posting(db: Session) -> None:
    u = User(preferences={})
    db.add(u)
    db.flush()
    app = Application(user_id=u.id, status=ApplicationStatus.DRAFTING, notes="字节豆包")
    app.job_posting = JobPosting(raw_text="JD text...", company_name="字节", job_title="PM")
    db.add(app)
    db.flush()
    assert app.job_posting.company_name == "字节"
    assert app.status == ApplicationStatus.DRAFTING
