from uuid import UUID

from src.ai.llm_client import LLMClient
from src.ai.prompts.parse_resume import PARSE_RESUME_SYSTEM, build_user_prompt
from src.models import PersonaType
from src.schemas.resume import ParsedResume

_PERSONA_HINTS: dict[PersonaType, str] = {
    PersonaType.FRESH_GRAD: "应届校招（项目以实习/课程/竞赛为主）",
    PersonaType.JOB_HOPPER: "社招跳槽（有完整工作经验）",
    PersonaType.CAREER_CHANGER: "跨行业转行（有完整工作经验但跨域）",
}

_llm = LLMClient()


async def parse_resume_text(
    text: str, persona_type: PersonaType | None, user_id: UUID
) -> ParsedResume:
    hint = _PERSONA_HINTS.get(persona_type or PersonaType.JOB_HOPPER, "")
    raw = await _llm.acomplete(
        model="auto-m1",
        system=PARSE_RESUME_SYSTEM,
        messages=[{"role": "user", "content": build_user_prompt(text, hint)}],
        max_tokens=4096,
        user_id=user_id,
        scene="resume_parse",
    )
    return ParsedResume.model_validate_json(raw)
