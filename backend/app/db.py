"""Database engine, session factory and the base class for ORM models."""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    """All ORM models inherit from this so Alembic can find their tables."""


# pool_pre_ping checks a connection is alive before using it, so the API
# recovers by itself if the database restarts.
engine = create_engine(get_settings().database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """FastAPI dependency: one database session per request, always closed."""
    with SessionLocal() as session:
        yield session
