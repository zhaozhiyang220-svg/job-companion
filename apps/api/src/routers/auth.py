from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.analytics import capture
from src.core.config import get_settings
from src.core.db import get_db
from src.models import User
from src.schemas.auth import MagicLinkRequest, MagicLinkVerify
from src.services.magic_link import request_link, verify_token
from src.services.wechat import build_qr_url, exchange_code_for_openid

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/magic-link/request")
def request_magic_link(body: MagicLinkRequest, db: Session = Depends(get_db)) -> dict[str, bool]:
    settings = get_settings()
    base = (
        "http://localhost:3000"
        if settings.app_env == "development"
        else "https://app.example.com"
    )
    request_link(db, body.email, base)
    return {"sent": True}


@router.post("/magic-link/verify")
def verify_magic_link(body: MagicLinkVerify, db: Session = Depends(get_db)) -> dict[str, str]:
    email_hash = verify_token(db, body.token)
    if not email_hash:
        raise HTTPException(status_code=400, detail="invalid or expired token")
    user = db.query(User).filter(User.email_lookup_hash == email_hash).first()
    if not user:
        user = User(email_lookup_hash=email_hash, preferences={})
        db.add(user)
        db.commit()
        db.refresh(user)
    capture(str(user.id), "user_signed_in", {"method": "magic_link"})
    return {"user_id": str(user.id), "session_token": "PLACEHOLDER_ISSUED_IN_TASK_9"}


@router.get("/wechat/qr")
def wechat_qr() -> dict[str, str]:
    qr, state = build_qr_url()
    return {"qr_url": qr, "state": state}


@router.get("/wechat/callback")
async def wechat_callback(
    code: str, state: str, db: Session = Depends(get_db)
) -> dict[str, str]:
    openid = await exchange_code_for_openid(code)
    user = db.query(User).filter(User.wechat_openid == openid).first()
    if not user:
        user = User(wechat_openid=openid, preferences={})
        db.add(user)
        db.commit()
        db.refresh(user)
    capture(str(user.id), "user_signed_in", {"method": "wechat"})
    return {"user_id": str(user.id), "session_token": "PLACEHOLDER_ISSUED_IN_TASK_9"}
