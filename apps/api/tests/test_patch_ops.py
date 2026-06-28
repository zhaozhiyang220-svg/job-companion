import pytest

from src.services.patch_ops import (
    RewriteTooLargeError,
    apply_operations,
    validate_rewrite_intensity,
)


def _master() -> dict[str, object]:
    return {
        "ability_cards": [{"id": "a1", "skill_name": "增长", "level": 3}],
        "project_cards": [
            {
                "id": "p1",
                "project_name": "拉新",
                "star": {
                    "situation": "",
                    "task": "",
                    "action": "",
                    "result": "达成全年拉新目标，新增注册用户超过五十万",
                },
            }
        ],
        "experience_cards": [
            {"id": "e1", "company": "字节", "title": "PM"},
            {"id": "e2", "company": "美团", "title": "PM"},
        ],
    }


def test_emphasize_marks_card() -> None:
    r = apply_operations(_master(), [{"type": "emphasize", "card_id": "a1", "intensity": "high"}])
    assert r["ability_cards"][0]["_emphasized"] == "high"  # type: ignore[index]


def test_hide_marks_card() -> None:
    r = apply_operations(_master(), [{"type": "hide", "card_id": "e2"}])
    e2 = next(c for c in r["experience_cards"] if c["id"] == "e2")  # type: ignore[attr-defined]
    assert e2["_hidden"] is True


def test_rewrite_within_threshold() -> None:
    r = apply_operations(
        _master(),
        [
            {
                "type": "rewrite",
                "card_id": "p1",
                "field": "star.result",
                "new_text": "达成全年拉新目标，新增注册用户超过五十万人",
            }
        ],
    )
    assert "五十万人" in r["project_cards"][0]["star"]["result"]  # type: ignore[index]


def test_rewrite_too_large_raises() -> None:
    with pytest.raises(RewriteTooLargeError):
        apply_operations(
            _master(),
            [
                {
                    "type": "rewrite",
                    "card_id": "a1",
                    "field": "skill_name",
                    "new_text": "完全不同的能力名字写很长很长很长",
                }
            ],
        )


def test_reorder_moves_card() -> None:
    r = apply_operations(_master(), [{"type": "reorder", "card_id": "e2", "new_position": 0}])
    assert r["experience_cards"][0]["id"] == "e2"  # type: ignore[index]


def test_insert_keyword_appends() -> None:
    r = apply_operations(
        _master(), [{"type": "insert_keyword", "card_id": "a1", "keywords": ["数据", "B2C"]}]
    )
    assert r["ability_cards"][0]["_inserted_keywords"] == ["数据", "B2C"]  # type: ignore[index]


def test_unknown_card_skipped() -> None:
    r = apply_operations(_master(), [{"type": "hide", "card_id": "nonexistent"}])
    assert r["ability_cards"][0]["_hidden"] is False  # type: ignore[index]


def test_validate_rewrite_intensity() -> None:
    assert validate_rewrite_intensity("hello world", "hello world!") is True
    assert validate_rewrite_intensity("hello world", "totally different text") is False
