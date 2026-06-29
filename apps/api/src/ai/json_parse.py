"""LLM 返回的 JSON 容错解析。

模型（尤其轻量档）有时不遵守"仅输出 JSON"，会用 ```json``` 代码块包裹或在前后
加解释文字，导致 json.loads/model_validate_json 直接 500。这里统一做清洗：
先剥 markdown 代码块，再在仍夹杂散文时切出最外层的 {…} 或 […]。
"""

import json
import re
from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def extract_json(raw: str) -> str:
    s = raw.strip()
    m = _FENCE.search(s)
    if m:
        s = m.group(1).strip()
    if s and s[0] not in "{[":
        starts = [i for i in (s.find("{"), s.find("[")) if i != -1]
        end = max(s.rfind("}"), s.rfind("]"))
        if starts and end > min(starts):
            s = s[min(starts) : end + 1]
    return s


def loads(raw: str) -> Any:
    """容错版 json.loads。"""
    return json.loads(extract_json(raw))


def validate(model: type[T], raw: str) -> T:
    """容错版 Model.model_validate_json。"""
    return model.model_validate_json(extract_json(raw))
