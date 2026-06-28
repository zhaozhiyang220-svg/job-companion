from cryptography.fernet import Fernet

from src.core.config import get_settings

_fernet = Fernet(get_settings().field_encryption_key.encode())


def encrypt_field(value: str) -> str:
    return _fernet.encrypt(value.encode()).decode()


def decrypt_field(value: str) -> str:
    return _fernet.decrypt(value.encode()).decode()
