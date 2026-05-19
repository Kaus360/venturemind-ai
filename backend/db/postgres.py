"""Async PostgreSQL infrastructure for VentureMind AI.

This module owns database bootstrapping for FastAPI services:
- creates a SQLAlchemy async engine backed by asyncpg
- exposes an async session factory
- provides a declarative Base for ORM models
- provides a FastAPI dependency for request-scoped sessions

Keep application models in ``backend/models`` and import ``Base`` from here
when declaring SQLAlchemy ORM tables.
"""

from __future__ import annotations

import logging
import os
from collections.abc import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

load_dotenv()

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""


def _normalize_database_url(database_url: str) -> str:
    """Ensure SQLAlchemy uses the asyncpg driver for PostgreSQL URLs."""

    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+asyncpg://", 1)

    return database_url


DATABASE_URL = _normalize_database_url(os.getenv("DATABASE_URL", ""))

if not DATABASE_URL:
    logger.warning("DATABASE_URL is not configured; database connections will fail until it is set.")


engine: AsyncEngine = create_async_engine(
    DATABASE_URL or "postgresql+asyncpg://invalid:invalid@localhost:5432/invalid",
    echo=os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true",
    pool_pre_ping=True,
    pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
    pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a request-scoped async DB session.

    The dependency commits nothing automatically. Route handlers and services
    should explicitly commit successful write transactions so read-only
    endpoints do not accidentally mutate state.
    """

    async with AsyncSessionLocal() as session:
        try:
            yield session
        except (OperationalError, DBAPIError) as exc:
            await session.rollback()
            logger.exception("PostgreSQL connection error during request.")
            raise RuntimeError("Database connection failed.") from exc
        except SQLAlchemyError as exc:
            await session.rollback()
            logger.exception("SQLAlchemy error during request.")
            raise RuntimeError("Database operation failed.") from exc
        except Exception:
            await session.rollback()
            logger.exception("Unexpected error during database session.")
            raise
        finally:
            await session.close()


async def verify_connection() -> bool:
    """Return True when PostgreSQL accepts a simple health-check query."""

    if not DATABASE_URL:
        logger.error("Cannot verify database connection because DATABASE_URL is missing.")
        return False

    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return True
    except (OperationalError, DBAPIError, OSError) as exc:
        logger.exception("Failed to connect to PostgreSQL.")
        raise RuntimeError("Unable to connect to PostgreSQL.") from exc


async def close_db_connections() -> None:
    """Dispose the async engine during FastAPI shutdown."""

    try:
        await engine.dispose()
    except SQLAlchemyError as exc:
        logger.exception("Failed to dispose PostgreSQL engine.")
        raise RuntimeError("Failed to close PostgreSQL connections.") from exc
