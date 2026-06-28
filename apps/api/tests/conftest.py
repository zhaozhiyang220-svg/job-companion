from collections.abc import Iterator

import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

import src.models  # noqa: F401  确保所有模型注册到 Base.metadata
from src.core.config import get_settings
from src.core.db import Base


@pytest.fixture(scope="session", autouse=True)
def engine() -> Iterator[Engine]:
    e = create_engine(get_settings().database_url, future=True)
    Base.metadata.create_all(e)
    yield e
    Base.metadata.drop_all(e)


@pytest.fixture
def db(engine: Engine) -> Iterator[Session]:
    session_factory = sessionmaker(bind=engine)
    s = session_factory()
    yield s
    s.rollback()
    s.close()
