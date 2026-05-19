"""Async Alembic environment for VentureMind AI.

This module configures Alembic to work with SQLAlchemy's asyncio engine and
``postgresql+asyncpg`` database URLs. It imports all ORM models so
``alembic revision --autogenerate`` can inspect ``Base.metadata`` accurately.
"""

from __future__ import annotations

import asyncio
import logging
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, async_engine_from_config

from backend.db.postgres import Base
from backend.db import schemas  # noqa: F401 - imported for Alembic autogenerate

config = context.config
logger = logging.getLogger(__name__)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _database_url() -> str:
    """Return the migration database URL from the ``DATABASE_URL`` environment variable."""

    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL must be set before running Alembic migrations.")

    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+asyncpg://", 1)

    return database_url


def run_migrations_offline() -> None:
    """Run migrations without creating a database engine.

    Offline mode emits SQL from the migration scripts using the configured URL.
    This is useful for reviewing SQL in CI or generating migration artifacts.
    """

    try:
        context.configure(
            url=_database_url(),
            target_metadata=target_metadata,
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()
    except Exception:
        logger.exception("Alembic offline migration failed.")
        raise


def do_run_migrations(connection: Connection) -> None:
    """Run migrations using an already-open synchronous Alembic connection."""

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations using an async SQLAlchemy engine."""

    try:
        configuration = {"sqlalchemy.url": _database_url()}

        connectable: AsyncEngine = async_engine_from_config(
            configuration,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)

        await connectable.dispose()
    except Exception:
        logger.exception("Alembic online migration failed.")
        raise


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
