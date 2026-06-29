import json
from uuid import UUID

from sqlalchemy.orm import Session

from src.ai import json_parse
from src.ai.llm_client import LLMClient
from src.ai.prompts.diagnose_quality import DIAGNOSE_QUALITY_SYSTEM
from src.core.security import decrypt_field
from src.models import MasterResume
from src.schemas.diagnosis import DiagnosisReport

_llm = LLMClient()

# 综合分 < 此阈值判为"不合格简历"，引导用户去"AI 挖经历"重建
QUALIFIED_THRESHOLD = 30


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


async def diagnose(db: Session, master_resume_id: UUID, user_id: UUID) -> DiagnosisReport:
    r = db.get(MasterResume, master_resume_id)
    if not r:
        raise ValueError("not found")
    payload = json.dumps(_to_input(r), ensure_ascii=False)
    raw = await _llm.acomplete(
        model="auto-m1",
        system=DIAGNOSE_QUALITY_SYSTEM,
        messages=[{"role": "user", "content": payload}],
        max_tokens=4096,
        user_id=user_id,
        scene="resume_diagnose",
    )
    report = json_parse.validate(DiagnosisReport, raw)

    # 后端派生 qualified（综合分阈值），保证与前端判定一致
    report.qualified = report.structure.composite_score >= QUALIFIED_THRESHOLD

    # 逐卡标记低含金量（保留原能力）
    weak_ids: dict[tuple[str, str], list[str]] = {
        (w.type, w.id): w.reasons for w in report.weak_cards
    }
    for ac in r.ability_cards:
        ac.is_weak = ("ability", str(ac.id)) in weak_ids
    for pc in r.project_cards:
        pc.is_weak = ("project", str(pc.id)) in weak_ids
        pc.weak_reasons = weak_ids.get(("project", str(pc.id)), [])

    r.quality_score = report.structure.composite_score
    db.commit()
    return report
