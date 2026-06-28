from datetime import UTC, datetime, timedelta
from uuid import UUID

from cryptography.fernet import Fernet
from jose import JWTError, jwt

from src.core.config import get_settings

_fernet = Fernet(get_settings().field_encryption_key.encode())


def encrypt_field(value: str) -> str:
    return _fernet.encrypt(value.encode()).decode()


def decrypt_field(value: str) -> str:
    return _fernet.decrypt(value.encode()).decode()


def issue_session_token(user_id: UUID) -> str:
    s = get_settings()
    payload = {
        "sub": str(user_id),
        "iat": datetime.now(UTC),
        "exp": datetime.now(UTC) + timedelta(hours=s.jwt_expires_hours),
    }
    return jwt.encode(payload, s.jwt_secret, algorithm=s.jwt_alg)


def verify_session_token(token: str) -> UUID | None:
    s = get_settings()
    try:
        payload = jwt.decode(token, s.jwt_secret, algorithms=[s.jwt_alg])
        return UUID(payload["sub"])
    except (JWTError, ValueError, KeyError):
        return None
