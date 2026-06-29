import json
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from src.core.db import SessionLocal
from src.core.security import issue_session_token
from src.main import app
from src.models import AbilityCard, MasterResume, User


def _setup() -> tuple[TestClient, str]:
    db = SessionLocal()
    u = User(preferences={})
    db.add(u)
    db.commit()
    db.refresh(u)
    r = MasterResume(user_id=u.id)
    db.add(r)
    db.flush()
    a = AbilityCard(master_resume_id=r.id, skill_name="Python", level=3)
    db.add(a)
    db.commit()
    aid = str(a.id)
    c = TestClient(app)
    c.cookies.set("jc_session", issue_session_token(u.id))
    db.close()
    return c, aid


def _report(aid: str, composite: int) -> dict[str, object]:
    return {
        "target_industry": "后端工程师",
        "structure": {
            "module_completeness": {"score": 4, "comment": "ok"},
            "module_order": {"score": 4, "comment": "ok"},
            "length_control": {"score": 3, "comment": "ok"},
            "readability": {"score": 3, "comment": "ok"},
            "composite_score": composite,
        },
        "ats": {
            "format_risks": [],
            "keyword_density_comment": "一般",
            "missing_keywords": ["Docker"],
            "weak_verbs": {"ratio_pct": 10, "comment": "少", "examples": ["负责"]},
        },
        "highlights_issues": {"issues": ["缺数据"], "highlights": ["带团队"]},
        "industry_benchmark": [
            {"dimension": "项目深度", "expected": "深", "current": "浅", "gap": "补"}
        ],
        "fix_priorities": {"urgent": ["加数据"], "important": [], "nice_to_have": []},
        "weak_cards": [{"type": "ability", "id": aid, "reasons": ["evidence missing"]}],
    }


def test_diagnose_returns_report_and_marks_weak() -> None:
    c, aid = _setup()
    with patch(
        "src.services.quality_diagnoser._llm.acomplete",
        AsyncMock(return_value=json.dumps(_report(aid, 65), ensure_ascii=False)),
    ):
        r = c.post("/api/v1/master-resume/diagnose")
    assert r.status_code == 200
    body = r.json()
    assert body["structure"]["composite_score"] == 65
    assert body["qualified"] is True
    assert body["target_industry"] == "后端工程师"
    assert len(body["industry_benchmark"]) == 1
    assert body["weak_cards"][0]["id"] == aid


def test_diagnose_low_score_is_unqualified() -> None:
    c, aid = _setup()
    with patch(
        "src.services.quality_diagnoser._llm.acomplete",
        AsyncMock(return_value=json.dumps(_report(aid, 20), ensure_ascii=False)),
    ):
        r = c.post("/api/v1/master-resume/diagnose")
    assert r.status_code == 200
    assert r.json()["qualified"] is False
