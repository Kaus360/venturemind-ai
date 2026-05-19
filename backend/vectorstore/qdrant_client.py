"""Async Qdrant client infrastructure for VentureMind AI.

This module centralizes Qdrant connection management and collection bootstrap
logic. FastAPI startup hooks should call ``create_collections()``, route
dependencies can use ``get_qdrant_client()``, and shutdown hooks should call
``close_qdrant_client()``.
"""

from __future__ import annotations

import logging
import os
from collections.abc import AsyncGenerator
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models

from backend.vectorstore.embedding_pipeline import EMBEDDING_DIMENSION

load_dotenv()

logger = logging.getLogger(__name__)

VECTOR_SIZE = int(os.getenv("QDRANT_VECTOR_SIZE", str(EMBEDDING_DIMENSION)))
STARTUP_COLLECTION = os.getenv("QDRANT_STARTUP_COLLECTION", "startup_embeddings")
COMPETITOR_COLLECTION = os.getenv("QDRANT_COMPETITOR_COLLECTION", "competitor_embeddings")
QDRANT_COLLECTIONS = (STARTUP_COLLECTION, COMPETITOR_COLLECTION)


class QdrantClientError(RuntimeError):
    """Raised when Qdrant setup, health checks, or cleanup fail."""


class QdrantHealthStatus(BaseModel):
    """Structured Qdrant health-check result."""

    is_healthy: bool = Field(description="Whether Qdrant responded successfully.")
    url: str = Field(description="Configured Qdrant endpoint.")
    collections: list[str] = Field(description="Expected VentureMind AI collections.")


class CollectionSetupResult(BaseModel):
    """Result of creating or verifying required Qdrant collections."""

    created: list[str] = Field(default_factory=list)
    existing: list[str] = Field(default_factory=list)
    vector_size: int
    distance: str


def _get_qdrant_url() -> str:
    """Read the Qdrant URL from environment with a local development default."""

    return os.getenv("QDRANT_URL", "http://localhost:6333")


@lru_cache(maxsize=1)
def _build_qdrant_client() -> AsyncQdrantClient:
    """Create one process-wide async Qdrant client."""

    api_key = os.getenv("QDRANT_API_KEY") or None
    timeout = float(os.getenv("QDRANT_TIMEOUT_SECONDS", "10"))

    return AsyncQdrantClient(
        url=_get_qdrant_url(),
        api_key=api_key,
        timeout=timeout,
    )


def get_client() -> AsyncQdrantClient:
    """Return the cached process-wide async Qdrant client."""

    return _build_qdrant_client()


async def get_qdrant_client() -> AsyncGenerator[AsyncQdrantClient, None]:
    """FastAPI dependency that yields the process-wide async Qdrant client."""

    try:
        yield get_client()
    except Exception as exc:
        logger.exception("Qdrant client dependency failed.")
        raise QdrantClientError("Qdrant client dependency failed.") from exc


async def create_collections() -> CollectionSetupResult:
    """Create VentureMind AI vector collections when they do not already exist."""

    client = get_client()
    created: list[str] = []
    existing: list[str] = []

    try:
        for collection_name in QDRANT_COLLECTIONS:
            exists = await client.collection_exists(collection_name=collection_name)
            if exists:
                existing.append(collection_name)
                continue

            await client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=VECTOR_SIZE,
                    distance=models.Distance.COSINE,
                ),
            )
            created.append(collection_name)
    except Exception as exc:
        logger.exception("Failed to create or verify Qdrant collections.")
        raise QdrantClientError("Failed to create or verify Qdrant collections.") from exc

    return CollectionSetupResult(
        created=created,
        existing=existing,
        vector_size=VECTOR_SIZE,
        distance=models.Distance.COSINE.value,
    )


async def health_check() -> QdrantHealthStatus:
    """Verify that Qdrant is reachable and able to list collections."""

    client = get_client()

    try:
        await client.get_collections()
    except Exception as exc:
        logger.exception("Qdrant health check failed.")
        raise QdrantClientError("Qdrant health check failed.") from exc

    return QdrantHealthStatus(
        is_healthy=True,
        url=_get_qdrant_url(),
        collections=list(QDRANT_COLLECTIONS),
    )


async def close_qdrant_client() -> None:
    """Close the cached Qdrant client during application shutdown."""

    try:
        if _build_qdrant_client.cache_info().currsize == 0:
            return

        await _build_qdrant_client().close()
        _build_qdrant_client.cache_clear()
    except Exception as exc:
        logger.exception("Failed to close Qdrant client.")
        raise QdrantClientError("Failed to close Qdrant client.") from exc
