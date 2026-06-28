import json
from typing import Any
from uuid import UUID

from src.ai.llm_client import LLMClient
from src.ai.prompts.summarize_resource import SUMMARIZE_RESOURCE_SYSTEM
from src.models.resource_item import ResourceType

_llm = LLMClient()


async def summarize(text: str, type_: ResourceType, user_id: UUID) -> dict[str, Any]:
    raw = await _llm.acomplete(
        model="auto-light",
        system=SUMMARIZE_RESOURCE_SYSTEM,
        messages=[
            {"role": "user", "content": f"类型：{type_.value}\n\n原文：\n{text[:6000]}"}
        ],
        max_tokens=512,
        user_id=user_id,
        scene="resource_summarize",
    )
    data: dict[str, Any] = json.loads(raw)
    return data
