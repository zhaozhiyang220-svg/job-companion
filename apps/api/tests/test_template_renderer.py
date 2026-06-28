from src.services.template_renderer import render_html


def _data() -> dict[str, object]:
    return {
        "basic_info": {"name": "张三", "email": "a@b.com"},
        "experience_cards": [
            {
                "id": "e1",
                "company": "字节",
                "title": "PM",
                "period": "2020-至今",
                "is_current": True,
                "_emphasized": "high",
                "_hidden": False,
            },
        ],
        "project_cards": [],
        "ability_cards": [{"id": "a1", "skill_name": "增长", "level": 4}],
    }


def test_zh_renders_with_mask() -> None:
    html = render_html(_data(), "zh", mask_current_company=True)
    assert "某知名互联网公司" in html
    assert "字节" not in html
    assert "张三" in html


def test_en_renders_without_mask() -> None:
    html = render_html(_data(), "en", mask_current_company=False)
    assert "字节" in html
    assert "Experience" in html
