from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

TPL_DIR = Path(__file__).parent.parent / "templates" / "resume"
_env = Environment(
    loader=FileSystemLoader(str(TPL_DIR)), autoescape=select_autoescape(["html"])
)
_CSS = (TPL_DIR / "base.css").read_text(encoding="utf-8")

MASK_LABELS = {
    "zh": "某知名互联网公司",
    "en": "Major Tech Company",
}


def _filter(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [c for c in cards if not c.get("_hidden")]


def render_html(rendered: dict[str, object], language: str, mask_current_company: bool) -> str:
    data: dict[str, Any] = rendered
    tpl = _env.get_template("zh_simple.html" if language == "zh" else "en_simple.html")
    basic = data.get("basic_info", {})
    experiences = _filter(data.get("experience_cards", []))
    mask = MASK_LABELS.get(language, MASK_LABELS["zh"])
    for e in experiences:
        if mask_current_company and e.get("is_current"):
            e["company_display"] = mask
        else:
            e["company_display"] = e.get("company", "")
    return tpl.render(
        css=_CSS,
        basic=basic,
        experiences=experiences,
        projects=_filter(data.get("project_cards", [])),
        abilities=_filter(data.get("ability_cards", [])),
    )
