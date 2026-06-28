from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.core.security import verify_session_token
from src.models import User


def current_user(
    jc_session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not jc_session:
        raise HTTPException(status_code=401, detail="unauthenticated")
    uid = verify_session_token(jc_session)
    if not uid:
        raise HTTPException(status_code=401, detail="invalid session")
    user = db.get(User, uid)
    if not user:
        raise HTTPException(status_code=401, detail="user not found")
    return user
