import json
from typing import Any
from uuid import UUID

from src.ai import json_parse
from src.ai.llm_client import LLMClient
from src.ai.prompts.weekly_observation import WEEKLY_OBSERVATION_SYSTEM

_llm = LLMClient()


async def generate_observation(
    stats: dict[str, int], sample_jds: list[dict[str, object]], user_id: UUID
) -> dict[str, Any]:
    payload = {"stats": stats, "new_jds": sample_jds}
    raw = await _llm.acomplete(
        model="auto-m1",
        system=WEEKLY_OBSERVATION_SYSTEM,
        messages=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
        max_tokens=512,
        user_id=user_id,
        scene="weekly_observation",
    )
    data: dict[str, Any] = json_parse.loads(raw)
    return data
