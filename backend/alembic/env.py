"""Alembic entry point: tells migrations which database and which models to use."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

import app.models  # noqa: F401  (registers the tables on Base.metadata)
from app.core.config import get_settings
from app.db import Base

config = context.config
if config.config_file_name is not None:
    # Keep loggers created before this point (e.g. by pytest) working.
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def run_migrations() -> None:
    engine = create_engine(get_settings().database_url)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


run_migrations()
