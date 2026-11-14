"""Shared test setup.

Tests run against a real PostGIS database (never SQLite) because the spatial
queries are the part of this project most worth testing. Start one with
`docker compose up -d db`.
"""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

# 127.0.0.1 rather than "localhost": on Windows, localhost can resolve to IPv6
# first, and the database port is only published on IPv4, so connecting hangs.
DEFAULT_TEST_URL = "postgresql+psycopg://pothole:change-me@127.0.0.1:5432/pothole_test"
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", DEFAULT_TEST_URL)

# Must be set before any `app` module is imported, because the engine is
# created at import time from this setting.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

BACKEND_DIR = Path(__file__).resolve().parents[1]


def _create_database_if_missing(url: str) -> None:
    target = make_url(url)
    admin_engine = create_engine(target.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": target.database}
        ).scalar()
        if not exists:
            # Identifiers cannot be bound parameters; the name comes from our own config.
            conn.execute(text(f'CREATE DATABASE "{target.database}"'))
    admin_engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> None:
    """Create the test database once and bring it to the latest migration."""
    from alembic import command
    from alembic.config import Config

    _create_database_if_missing(TEST_DATABASE_URL)
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    command.upgrade(config, "head")


@pytest.fixture
def db() -> Iterator:
    """A session whose changes are rolled back after each test.

    Every test starts from the same empty tables, so tests cannot affect
    each other and can run in any order.
    """
    from sqlalchemy.orm import Session

    from app.db import engine

    with engine.connect() as connection:
        transaction = connection.begin()
        session = Session(bind=connection, join_transaction_mode="create_savepoint")
        try:
            yield session
        finally:
            session.close()
            transaction.rollback()


@pytest.fixture
def client(db) -> Iterator:
    """A test client whose requests use the same rolled-back session."""
    from fastapi.testclient import TestClient

    from app.db import get_db
    from app.main import app

    app.dependency_overrides[get_db] = lambda: db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
