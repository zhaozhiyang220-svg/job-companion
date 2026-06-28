from src.core.config import Settings


def test_settings_loads_from_env(monkeypatch: object) -> None:
    import os

    os.environ["DATABASE_URL"] = "postgresql+psycopg://x:y@h:5432/d"
    os.environ["JWT_SECRET"] = "a" * 32
    os.environ["FIELD_ENCRYPTION_KEY"] = "k" * 44
    s = Settings()  # type: ignore[call-arg]
    assert s.database_url.startswith("postgresql")
    assert s.jwt_alg == "HS256"
