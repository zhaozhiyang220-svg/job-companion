from uuid import uuid4

from src.core.security import issue_session_token, verify_session_token


def test_jwt_roundtrip() -> None:
    uid = uuid4()
    tok = issue_session_token(uid)
    assert verify_session_token(tok) == uid


def test_jwt_invalid_returns_none() -> None:
    assert verify_session_token("bogus") is None
