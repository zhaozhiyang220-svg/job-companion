import importlib
import os


def test_app_starts_without_sentry_dsn() -> None:
    os.environ.pop("SENTRY_DSN", None)
    mod = importlib.reload(importlib.import_module("src.main"))
    assert mod.app is not None
