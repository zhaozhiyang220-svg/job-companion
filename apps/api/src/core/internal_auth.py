from fastapi import Header, HTTPException

from src.core.config import get_settings


def require_internal_password(x_internal_password: str | None = Header(default=None)) -> None:
    expected = get_settings().internal_dashboard_password
    if not expected:
        raise HTTPException(503, "internal dashboard disabled (set INTERNAL_DASHBOARD_PASSWORD)")
    if x_internal_password != expected:
        raise HTTPException(401, "wrong internal password")
