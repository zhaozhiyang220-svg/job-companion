import json
from typing import Any
from uuid import UUID

from src.ai import json_parse
from src.ai.llm_client import LLMClient
from src.ai.prompts.generate_patch import GENERATE_PATCH_SYSTEM

_llm = LLMClient()


async def generate_patch(
    master_serialized: dict[str, object],
    jd_serialized: dict[str, object],
    language: str,
    user_id: UUID,
) -> dict[str, object]:
    """基于主简历 + JD 生成 PatchOperations + 修改理由。

    注：MiniMax Context Caching（把 master 作为缓存前缀降成本）是后续优化，
    需 LLMClient + Redis 支持 extra_body/cache_id；v1 先走直连。
    """
    payload = json.dumps(
        {"master": master_serialized, "jd": jd_serialized, "output_language": language},
        ensure_ascii=False,
    )
    raw = await _llm.acomplete(
        model="auto-m1",
        system=GENERATE_PATCH_SYSTEM,
        messages=[{"role": "user", "content": payload}],
        max_tokens=2048,
        user_id=user_id,
        scene="patch_generate",
    )
    data: dict[str, Any] = json_parse.loads(raw)
    if "patch" not in data or "reasoning" not in data:
        raise ValueError("invalid patch generator response")
    return data
