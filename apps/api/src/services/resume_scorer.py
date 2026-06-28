import json
from uuid import UUID

from src.ai.llm_client import LLMClient
from src.ai.prompts.score_resume import SCORE_RESUME_SYSTEM

_llm = LLMClient()


async def score_branch(rendered: dict[str, object], jd: dict[str, object], user_id: UUID) -> int:
    raw = await _llm.acomplete(
        model="auto-light",
        system=SCORE_RESUME_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": json.dumps({"resume": rendered, "jd": jd}, ensure_ascii=False),
            }
        ],
        max_tokens=128,
        user_id=user_id,
        scene="resume_score",
    )
    return int(json.loads(raw)["score"])
