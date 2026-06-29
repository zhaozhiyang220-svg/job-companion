from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from src.core.analytics import capture
from src.core.config import get_settings
from src.core.db import get_db
from src.core.security import issue_session_token, verify_session_token
from src.models import User
from src.schemas.auth import MagicLinkRequest, MagicLinkVerify
from src.services.magic_link import request_link, verify_token
from src.services.wechat import build_qr_url, exchange_code_for_openid

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

_COOKIE_MAX_AGE = 60 * 60 * 24 * 30  # 30 天


def _set_session_cookie(response: Response, user: User) -> None:
    token = issue_session_token(user.id)
    response.set_cookie(
        "jc_session",
        token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=_COOKIE_MAX_AGE,
    )


@router.post("/guest")
def create_guest(
    response: Response,
    jc_session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    # 免登录访客：首次访问自动建一个匿名用户并下发 session，现有受保护接口即可使用。
    # 幂等：已有有效会话则直接返回，避免重复创建访客。
    if jc_session:
        uid = verify_session_token(jc_session)
        if uid and db.get(User, uid):
            return {"user_id": str(uid)}
    user = User(preferences={})
    db.add(user)
    db.commit()
    db.refresh(user)
    _set_session_cookie(response, user)
    capture(str(user.id), "guest_session_created", {})
    return {"user_id": str(user.id)}


@router.post("/magic-link/request")
def request_magic_link(body: MagicLinkRequest, db: Session = Depends(get_db)) -> dict[str, bool]:
    settings = get_settings()
    request_link(db, body.email, settings.public_web_url)
    return {"sent": True}


@router.post("/magic-link/verify")
def verify_magic_link(
    body: MagicLinkVerify, response: Response, db: Session = Depends(get_db)
) -> dict[str, str]:
    email_hash = verify_token(db, body.token)
    if not email_hash:
        raise HTTPException(status_code=400, detail="invalid or expired token")
    user = db.query(User).filter(User.email_lookup_hash == email_hash).first()
    if not user:
        user = User(email_lookup_hash=email_hash, preferences={})
        db.add(user)
        db.commit()
        db.refresh(user)
    _set_session_cookie(response, user)
    capture(str(user.id), "user_signed_in", {"method": "magic_link"})
    return {"user_id": str(user.id)}


@router.get("/wechat/qr")
def wechat_qr() -> dict[str, str]:
    qr, state = build_qr_url()
    return {"qr_url": qr, "state": state}


@router.get("/wechat/callback")
async def wechat_callback(
    code: str, state: str, response: Response, db: Session = Depends(get_db)
) -> dict[str, str]:
    openid = await exchange_code_for_openid(code)
    user = db.query(User).filter(User.wechat_openid == openid).first()
    if not user:
        user = User(wechat_openid=openid, preferences={})
        db.add(user)
        db.commit()
        db.refresh(user)
    _set_session_cookie(response, user)
    capture(str(user.id), "user_signed_in", {"method": "wechat"})
    return {"user_id": str(user.id)}
