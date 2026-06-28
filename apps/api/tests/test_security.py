from src.core.security import decrypt_field, encrypt_field


def test_encrypt_decrypt_roundtrip() -> None:
    plain = "user@example.com"
    enc = encrypt_field(plain)
    assert enc != plain
    assert decrypt_field(enc) == plain
