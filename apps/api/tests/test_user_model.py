from sqlalchemy.orm import Session

from src.models import PersonaType, User


def test_user_can_be_created_with_persona(db: Session) -> None:
    u = User(nickname="测试", persona_type=PersonaType.JOB_HOPPER, preferences={})
    db.add(u)
    db.flush()
    assert u.id is not None
    assert u.persona_type == PersonaType.JOB_HOPPER
