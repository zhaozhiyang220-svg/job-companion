from sqlalchemy.orm import Session

from src.models import CoachInquiry, CoachInquiryStatus, User


def test_create_inquiry(db: Session) -> None:
    u = User(preferences={})
    db.add(u)
    db.flush()
    ci = CoachInquiry(
        user_id=u.id, source_screen="resume_workspace", contact_method="wx:zhangsan"
    )
    db.add(ci)
    db.flush()
    assert ci.status == CoachInquiryStatus.NEW
