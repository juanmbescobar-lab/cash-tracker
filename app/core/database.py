"""SQLAlchemy engine and session factory.

The engine is created lazily based on the current settings. Sessions
are obtained via ``SessionLocal()`` or, inside FastAPI endpoints, via
the ``get_db`` dependency.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

_settings = get_settings()

# SQLite-specific: same connection across threads requires this flag.
# For non-SQLite databases this argument is ignored.
_connect_args = {"check_same_thread": False} if _settings.database_url.startswith("sqlite") else {}

engine = create_engine(
    _settings.database_url,
    connect_args=_connect_args,
    echo=_settings.debug,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models.

    All domain models (Transaction, Category, etc.) should inherit
    from this class so Alembic can discover them.
    """


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session.

    Ensures the session is closed after the request, regardless of
    whether an exception was raised.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
