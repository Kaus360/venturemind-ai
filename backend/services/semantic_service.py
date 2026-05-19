"""Core semantic intelligence service for VentureMind AI.

This service coordinates startup text chunking, embedding generation, Qdrant
vector persistence, PostgreSQL metadata persistence, and similarity search
response shaping. It deliberately keeps FastAPI concerns out of the module so
routes can call these functions with an injected ``AsyncSession``.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from qdrant_client.http import models as qdrant_models
from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.postgres import AsyncSessionLocal
from backend.db.schemas import EmbeddingMetadata
from backend.models.embedding_model import (
    SimilarityResult,
    SimilaritySearchRequest,
    SimilaritySearchResponse,
    StartupEmbedRequest,
    StartupEmbedResponse,
)
from backend.vectorstore.chunking import chunk_and_embed_with_metadata
from backend.vectorstore.embedding_pipeline import generate_embedding
from backend.vectorstore.qdrant_client import STARTUP_COLLECTION, get_client
from backend.vectorstore.vector_search import (
    VectorSearchError,
    VectorUpsertError,
    search_similar,
    upsert_vector,
)

logger = logging.getLogger(__name__)


class SemanticServiceError(RuntimeError):
    """Base exception for semantic intelligence service failures."""


class StartupEmbeddingError(SemanticServiceError):
    """Raised when startup embedding or persistence fails."""


class StartupSimilaritySearchError(SemanticServiceError):
    """Raised when semantic startup search fails."""


class StartupEmbeddingDeletionError(SemanticServiceError):
    """Raised when startup embedding cleanup fails."""


def _build_startup_embedding_text(request: StartupEmbedRequest) -> str:
    """Combine startup fields into one semantic source document."""

    return "\n".join(
        [
            f"Title: {request.title}",
            f"Domain: {request.domain}",
            f"Target users: {request.target_users}",
            f"Description: {request.description}",
        ]
    )


def _build_embedding_id(startup_id: UUID, chunk_index: int) -> str:
    """Create a deterministic Qdrant point id for a startup chunk."""

    return f"startup:{startup_id}:chunk:{chunk_index}"


def _build_payload(
    request: StartupEmbedRequest,
    chunk: str,
    chunk_index: int,
    chunk_count: int,
) -> dict[str, Any]:
    """Build the Qdrant payload used for filtering and response hydration."""

    return {
        "startup_id": str(request.startup_id),
        "title": request.title,
        "domain": request.domain,
        "target_users": request.target_users,
        "chunk": chunk,
        "chunk_index": chunk_index,
        "chunk_count": chunk_count,
    }


async def embed_and_store_startup(
    request: StartupEmbedRequest,
    db: AsyncSession,
) -> StartupEmbedResponse:
    """Embed a startup profile, store vectors in Qdrant, and persist metadata.

    Args:
        request: Validated startup embedding request.
        db: Request-scoped SQLAlchemy async session from ``get_db``.

    Returns:
        A structured response describing the stored vector batch.
    """

    source_text = _build_startup_embedding_text(request)

    try:
        chunk_embeddings = await chunk_and_embed_with_metadata(source_text)
        chunk_count = len(chunk_embeddings.chunks)

        if chunk_count == 0:
            raise StartupEmbeddingError("Startup text produced no embeddable chunks.")

        first_embedding_id = _build_embedding_id(request.startup_id, 0)

        # Deterministic vector ids make Qdrant upserts idempotent. Mirror that
        # behavior in PostgreSQL by replacing metadata rows for this startup.
        await db.execute(
            delete(EmbeddingMetadata).where(
                EmbeddingMetadata.startup_id == request.startup_id,
                EmbeddingMetadata.vector_db == STARTUP_COLLECTION,
            )
        )

        for chunk_index, vector in enumerate(chunk_embeddings.embeddings):
            embedding_id = _build_embedding_id(request.startup_id, chunk_index)
            payload = _build_payload(
                request=request,
                chunk=chunk_embeddings.chunks[chunk_index],
                chunk_index=chunk_index,
                chunk_count=chunk_count,
            )

            await upsert_vector(
                collection=STARTUP_COLLECTION,
                id=embedding_id,
                vector=vector,
                payload=payload,
            )

            db.add(
                EmbeddingMetadata(
                    startup_id=request.startup_id,
                    embedding_id=embedding_id,
                    vector_db=STARTUP_COLLECTION,
                )
            )

        await db.commit()

        return StartupEmbedResponse(
            startup_id=request.startup_id,
            embedding_id=first_embedding_id,
            vector_db=STARTUP_COLLECTION,
            chunk_count=chunk_count,
            status="stored",
        )
    except (VectorUpsertError, SQLAlchemyError, ValueError) as exc:
        await db.rollback()
        logger.exception("Failed to embed and store startup %s.", request.startup_id)
        raise StartupEmbeddingError("Failed to embed and store startup.") from exc
    except Exception as exc:
        await db.rollback()
        logger.exception("Unexpected startup embedding failure for %s.", request.startup_id)
        raise StartupEmbeddingError("Unexpected startup embedding failure.") from exc


async def search_similar_startups(
    request: SimilaritySearchRequest,
) -> SimilaritySearchResponse:
    """Search for startups semantically similar to a query."""

    try:
        query_vector = await generate_embedding(request.query_text)
        filters = {"domain": request.domain_filter} if request.domain_filter else None
        search_response = await search_similar(
            collection=STARTUP_COLLECTION,
            query_vector=query_vector,
            top_k=request.top_k,
            filters=filters,
        )
    except (VectorSearchError, ValueError) as exc:
        logger.exception("Failed to search similar startups.")
        raise StartupSimilaritySearchError("Failed to search similar startups.") from exc
    except Exception as exc:
        logger.exception("Unexpected semantic search failure.")
        raise StartupSimilaritySearchError("Unexpected semantic search failure.") from exc

    results: list[SimilarityResult] = []
    seen_startups: set[str] = set()

    for match in search_response.results:
        payload = match.payload
        startup_id = payload.get("startup_id")

        # Multiple chunks can match the same startup. Keep the highest-ranked
        # chunk only, because Qdrant returns matches in descending score order.
        if not startup_id or startup_id in seen_startups:
            continue

        try:
            results.append(
                SimilarityResult(
                    startup_id=UUID(str(startup_id)),
                    title=str(payload.get("title", "")),
                    score=match.score,
                    domain=str(payload.get("domain", "")),
                    target_users=str(payload.get("target_users", "")),
                )
            )
            seen_startups.add(str(startup_id))
        except (TypeError, ValueError) as exc:
            logger.warning("Skipping malformed Qdrant payload: %s", exc)

    return SimilaritySearchResponse(
        query_text=request.query_text,
        results=results,
    )


async def delete_startup_embeddings(startup_id: str) -> dict[str, Any]:
    """Delete all Qdrant vectors and metadata rows for a startup.

    This function creates its own database session because the requested
    signature does not accept an injected session.
    """

    try:
        parsed_startup_id = UUID(startup_id)
    except ValueError as exc:
        raise StartupEmbeddingDeletionError("startup_id must be a valid UUID.") from exc

    try:
        await get_client().delete(
            collection_name=STARTUP_COLLECTION,
            points_selector=qdrant_models.FilterSelector(
                filter=qdrant_models.Filter(
                    must=[
                        qdrant_models.FieldCondition(
                            key="startup_id",
                            match=qdrant_models.MatchValue(value=str(parsed_startup_id)),
                        )
                    ]
                )
            ),
            wait=True,
        )

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                delete(EmbeddingMetadata).where(
                    EmbeddingMetadata.startup_id == parsed_startup_id,
                    EmbeddingMetadata.vector_db == STARTUP_COLLECTION,
                )
            )
            await db.commit()

        return {
            "startup_id": str(parsed_startup_id),
            "vector_db": STARTUP_COLLECTION,
            "metadata_deleted": int(result.rowcount or 0),
            "status": "deleted",
        }
    except SQLAlchemyError as exc:
        logger.exception("Failed to delete embedding metadata for startup %s.", startup_id)
        raise StartupEmbeddingDeletionError("Failed to delete embedding metadata.") from exc
    except Exception as exc:
        logger.exception("Failed to delete startup embeddings for %s.", startup_id)
        raise StartupEmbeddingDeletionError("Failed to delete startup embeddings.") from exc
