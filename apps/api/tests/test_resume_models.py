from sqlalchemy.orm import Session

from src.models import AbilityCard, ExperienceCard, MasterResume, ProjectCard, User


def test_resume_with_cards(db: Session) -> None:
    u = User(preferences={})
    db.add(u)
    db.flush()
    r = MasterResume(user_id=u.id, basic_info={"name": "张三"})
    r.ability_cards.append(AbilityCard(skill_name="增长", level=4))
    r.project_cards.append(ProjectCard(project_name="拉新增长"))
    r.experience_cards.append(
        ExperienceCard(company_encrypted="enc:xxx", title="PM", is_current=True)
    )
    db.add(r)
    db.flush()
    assert len(r.ability_cards) == 1
    assert r.experience_cards[0].is_current is True
