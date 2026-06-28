from uuid import UUID

from src.ai.llm_client import LLMClient
from src.ai.prompts.parse_jd import PARSE_JD_SYSTEM
from src.schemas.jd import ParsedJD

_llm = LLMClient()


async def parse_jd(text: str, user_id: UUID) -> ParsedJD:
    raw = await _llm.acomplete(
        model="auto-light",
        system=PARSE_JD_SYSTEM,
        messages=[{"role": "user", "content": text}],
        max_tokens=1024,
        user_id=user_id,
        scene="jd_parse",
    )
    return ParsedJD.model_validate_json(raw)
