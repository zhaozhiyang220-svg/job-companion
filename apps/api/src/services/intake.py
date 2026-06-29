import json
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from src.ai import json_parse
from src.ai.llm_client import LLMClient
from src.ai.prompts.intake_dialogue import (
    INTAKE_DIALOGUE_SYSTEM,
    INTAKE_FINALIZE_SYSTEM,
    INTAKE_FIRST_Q,
)
from src.models.intake_session import IntakeSession
from src.schemas.resume import ParsedResume

_llm = LLMClient()


def start(db: Session, user_id: UUID) -> tuple[UUID, str]:
    s = IntakeSession(
        user_id=user_id, transcript=[{"role": "assistant", "content": INTAKE_FIRST_Q}]
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s.id, INTAKE_FIRST_Q


async def answer(
    db: Session, session_id: UUID, user_id: UUID, user_msg: str
) -> dict[str, object]:
    s = db.get(IntakeSession, session_id)
    if not s or s.user_id != user_id:
        raise ValueError("session not found")
    s.transcript = [*s.transcript, {"role": "user", "content": user_msg}]
    raw = await _llm.acomplete(
        model="auto-light",
        system=INTAKE_DIALOGUE_SYSTEM,
        messages=s.transcript,
        max_tokens=512,
        user_id=user_id,
        scene="intake_dialogue",
    )
    data: dict[str, object] = json_parse.loads(raw)
    if data.get("done"):
        s.transcript = [
            *s.transcript,
            {"role": "assistant", "content": json.dumps(data, ensure_ascii=False)},
        ]
        db.commit()
        return {"done": True}
    next_q = str(data.get("next_question", ""))
    s.transcript = [*s.transcript, {"role": "assistant", "content": next_q}]
    db.commit()
    return {"done": False, "next_question": next_q}


async def finalize(db: Session, session_id: UUID, user_id: UUID) -> ParsedResume:
    s = db.get(IntakeSession, session_id)
    if not s or s.user_id != user_id:
        raise ValueError("session not found")
    raw = await _llm.acomplete(
        model="auto-m1",
        system=INTAKE_FINALIZE_SYSTEM,
        messages=[{"role": "user", "content": json.dumps(s.transcript, ensure_ascii=False)}],
        max_tokens=4096,
        user_id=user_id,
        scene="intake_finalize",
    )
    s.finished_at = datetime.now(UTC)
    db.commit()
    return json_parse.validate(ParsedResume, raw)
