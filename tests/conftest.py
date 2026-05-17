"""Shared pytest fixtures for the cash-tracker test suite."""

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session backed by an in-memory SQLite database.

    Each test gets its own isolated schema, created and destroyed within
    the test. Uses ``StaticPool`` so the in-memory database is shared
    across threads (FastAPI's TestClient runs in a separate thread).
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(  # noqa: N806
        bind=engine, autocommit=False, autoflush=False
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
