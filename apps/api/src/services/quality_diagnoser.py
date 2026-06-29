import json
from uuid import UUID

from sqlalchemy.orm import Session

from src.ai import json_parse
from src.ai.llm_client import LLMClient
from src.ai.prompts.diagnose_quality import DIAGNOSE_QUALITY_SYSTEM
from src.core.security import decrypt_field
from src.models import MasterResume

_llm = LLMClient()


def _to_input(r: MasterResume) -> dict[str, object]:
    return {
        "ability_cards": [
            {
                "id": str(c.id),
                "skill_name": c.skill_name,
                "evidence_text": c.evidence_text,
                "level": c.level,
                "last_used_year": c.last_used_year,
            }
            for c in r.ability_cards
        ],
        "project_cards": [
            {
                "id": str(c.id),
                "project_name": c.project_name,
                "role": c.role,
                "scale_data": c.scale_data,
                "star": c.star,
                "tech_stack": c.tech_stack,
            }
            for c in r.project_cards
        ],
        "experience_cards": [
            {
                "id": str(c.id),
                "company": decrypt_field(c.company_encrypted) if c.company_encrypted else "",
                "period": c.period,
                "title": c.title,
                "scope": c.scope,
                "achievements": c.achievements,
                "industry": c.industry,
            }
            for c in r.experience_cards
        ],
    }


async def diagnose(db: Session, master_resume_id: UUID, user_id: UUID) -> dict[str, object]:
    r = db.get(MasterResume, master_resume_id)
    if not r:
        raise ValueError("not found")
    payload = json.dumps(_to_input(r), ensure_ascii=False)
    raw = await _llm.acomplete(
        model="auto-m1",
        system=DIAGNOSE_QUALITY_SYSTEM,
        messages=[{"role": "user", "content": payload}],
        max_tokens=2048,
        user_id=user_id,
        scene="resume_diagnose",
    )
    result: dict[str, object] = json_parse.loads(raw)

    weak_raw = result.get("weak_cards", [])
    weak_ids: dict[tuple[str, str], list[str]] = {}
    if isinstance(weak_raw, list):
        for w in weak_raw:
            if isinstance(w, dict):
                reasons = w.get("reasons", [])
                weak_ids[(str(w.get("type")), str(w.get("id")))] = (
                    [str(x) for x in reasons] if isinstance(reasons, list) else []
                )

    # 注：ExperienceCard 不含 is_weak（v1 schema 仅 ability/project 标含金量）
    for ac in r.ability_cards:
        ac.is_weak = ("ability", str(ac.id)) in weak_ids
    for pc in r.project_cards:
        pc.is_weak = ("project", str(pc.id)) in weak_ids
        pc.weak_reasons = weak_ids.get(("project", str(pc.id)), [])

    score = result.get("overall_score")
    r.quality_score = int(score) if isinstance(score, int) else None
    db.commit()
    return result
