from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.core.deps import current_user
from src.models import PersonaType, User

router = APIRouter(prefix="/api/v1/me", tags=["me"])


class MeResponse(BaseModel):
    id: str
    nickname: str | None
    persona_type: PersonaType | None
    preferences: dict[str, object]


class MeUpdate(BaseModel):
    nickname: str | None = None
    persona_type: PersonaType | None = None
    preferences: dict[str, object] | None = None


def _serialize(user: User) -> MeResponse:
    return MeResponse(
        id=str(user.id),
        nickname=user.nickname,
        persona_type=user.persona_type,
        preferences=user.preferences or {},
    )


@router.get("")
def get_me(user: User = Depends(current_user)) -> MeResponse:
    return _serialize(user)


@router.patch("")
def update_me(
    body: MeUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> MeResponse:
    if body.nickname is not None:
        user.nickname = body.nickname
    if body.persona_type is not None:
        user.persona_type = body.persona_type
    if body.preferences is not None:
        user.preferences = body.preferences
    db.commit()
    db.refresh(user)
    return _serialize(user)
