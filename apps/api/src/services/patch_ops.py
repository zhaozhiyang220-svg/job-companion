import copy
from difflib import SequenceMatcher
from typing import Any, Literal, TypedDict


class ReorderOp(TypedDict):
    type: Literal["reorder"]
    card_id: str
    new_position: int


class EmphasizeOp(TypedDict):
    type: Literal["emphasize"]
    card_id: str
    intensity: Literal["low", "medium", "high"]


class RewriteOp(TypedDict):
    type: Literal["rewrite"]
    card_id: str
    field: str
    new_text: str


class HideOp(TypedDict):
    type: Literal["hide"]
    card_id: str


class InsertKeywordOp(TypedDict):
    type: Literal["insert_keyword"]
    card_id: str
    keywords: list[str]


Operation = ReorderOp | EmphasizeOp | RewriteOp | HideOp | InsertKeywordOp

VALID_TYPES = {"reorder", "emphasize", "rewrite", "hide", "insert_keyword"}
_COLLECTIONS = ("ability_cards", "project_cards", "experience_cards")


class RewriteTooLargeError(ValueError):
    """单字段改写超过 30% 字数上限。"""


def validate_rewrite_intensity(original: str, new: str, max_pct: float = 0.30) -> bool:
    if not original:
        return True
    ratio = SequenceMatcher(None, original, new).ratio()
    return (1 - ratio) <= max_pct


def apply_operations(master: dict[str, object], ops: list[dict[str, object]]) -> dict[str, object]:
    """将 ops 应用到 master 副本上，返回带标记的渲染版本。

    标记字段：_emphasized / _hidden / _patched_fields / _inserted_keywords。
    master 形状：{ability_cards: [...], project_cards: [...], experience_cards: [...]}。
    内部对动态字典用 Any 操作（签名仍是 dict[str, object]）。
    """
    result: dict[str, Any] = copy.deepcopy(master)
    index: dict[str, tuple[str, int]] = {}
    for coll in _COLLECTIONS:
        for i, c in enumerate(result.get(coll, [])):
            index[str(c.get("id"))] = (coll, i)
            c.setdefault("_emphasized", "none")
            c.setdefault("_hidden", False)
            c.setdefault("_patched_fields", [])
            c.setdefault("_inserted_keywords", [])

    for raw in ops:
        op: dict[str, Any] = raw
        t = op.get("type")
        if t not in VALID_TYPES:
            raise ValueError(f"unknown op type: {t}")
        cid = str(op.get("card_id"))
        if cid not in index:
            continue  # 未知卡片静默跳过
        coll, idx = index[cid]
        card = result[coll][idx]
        if t == "hide":
            card["_hidden"] = True
        elif t == "emphasize":
            card["_emphasized"] = op["intensity"]
        elif t == "rewrite":
            field = op["field"]
            if "." in field:
                top, sub = field.split(".", 1)
                original = str(card.get(top, {}).get(sub, ""))
            else:
                original = str(card.get(field, ""))
            if not validate_rewrite_intensity(original, op["new_text"]):
                raise RewriteTooLargeError(f"rewrite of {cid}.{field} exceeds 30% threshold")
            if "." in field:
                top, sub = field.split(".", 1)
                card.setdefault(top, {})[sub] = op["new_text"]
            else:
                card[field] = op["new_text"]
            card["_patched_fields"].append(field)
        elif t == "insert_keyword":
            card["_inserted_keywords"].extend(op["keywords"])
        elif t == "reorder":
            old = result[coll].pop(idx)
            new_pos = max(0, min(op["new_position"], len(result[coll])))
            result[coll].insert(new_pos, old)
            for i2, c2 in enumerate(result[coll]):
                index[str(c2["id"])] = (coll, i2)

    return result
