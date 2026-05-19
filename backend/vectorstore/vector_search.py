"""High-level async vector search operations for Qdrant.

The functions in this module are intentionally small service primitives:
upsert, search, get, and delete. They return Pydantic v2 models so FastAPI
routes can expose typed responses without leaking raw Qdrant SDK objects.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator
from qdrant_client.http import models

from backend.vectorstore.embedding_pipeline import EMBEDDING_DIMENSION
from backend.vectorstore.qdrant_client import get_client

logger = logging.getLogger(__name__)

DEFAULT_TOP_K = int(os.getenv("VECTOR_SEARCH_DEFAULT_TOP_K", "10"))

VectorId = int | str
Payload = dict[str, Any]
FilterValue = str | int | float | bool | list[str] | list[int] | list[float] | list[bool]
SearchFilters = dict[str, FilterValue] | models.Filter | None


class VectorStoreError(RuntimeError):
    """Base exception for vector search operations."""


class VectorUpsertError(VectorStoreError):
    """Raised when a vector cannot be inserted or updated."""


class VectorSearchError(VectorStoreError):
    """Raised when semantic search fails."""


class VectorDeleteError(VectorStoreError):
    """Raised when a vector cannot be deleted."""


class VectorGetError(VectorStoreError):
    """Raised when retrieving a vector fails."""


class VectorRecord(BaseModel):
    """Structured representation of a vector record returned by Qdrant."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: VectorId
    payload: Payload = Field(default_factory=dict)
    vector: list[float] | None = None


class VectorSearchResult(BaseModel):
    """One semantic search match."""

    id: VectorId
    score: float
    payload: Payload = Field(default_factory=dict)
    vector: list[float] | None = None


class VectorSearchResponse(BaseModel):
    """Structured semantic search response."""

    collection: str
    top_k: int
    results: list[VectorSearchResult]


class VectorOperationResponse(BaseModel):
    """Structured response for upsert and delete operations."""

    collection: str
    id: VectorId
    status: str


class VectorGetResponse(BaseModel):
    """Structured response for point retrieval."""

    collection: str
    found: bool
    record: VectorRecord | None = None


class VectorPayload(BaseModel):
    """Validated input model for vector writes."""

    collection: str
    id: VectorId
    vector: list[float]
    payload: Payload = Field(default_factory=dict)

    @field_validator("vector")
    @classmethod
    def validate_vector_dimension(cls, vector: list[float]) -> list[float]:
        """Ensure stored vectors match the configured embedding dimension."""

        if len(vector) != EMBEDDING_DIMENSION:
            raise ValueError(f"vector must contain {EMBEDDING_DIMENSION} dimensions.")
        return vector


def _build_filter(filters: SearchFilters) -> models.Filter | None:
    """Convert simple field-value filters into a Qdrant filter object."""

    if filters is None or isinstance(filters, models.Filter):
        return filters

    conditions: list[models.FieldCondition] = []
    for field_name, value in filters.items():
        if isinstance(value, list):
            conditions.append(
                models.FieldCondition(
                    key=field_name,
                    match=models.MatchAny(any=value),
                )
            )
        else:
            conditions.append(
                models.FieldCondition(
                    key=field_name,
                    match=models.MatchValue(value=value),
                )
            )

    return models.Filter(must=conditions) if conditions else None


def _extract_vector(vector: Any) -> list[float] | None:
    """Normalize Qdrant vector payloads into a plain list when present."""

    if vector is None:
        return None

    if isinstance(vector, list):
        return [float(item) for item in vector]

    if isinstance(vector, dict):
        first_vector = next(iter(vector.values()), None)
        if isinstance(first_vector, list):
            return [float(item) for item in first_vector]

    return None


async def upsert_vector(
    collection: str,
    id: VectorId,
    vector: list[float],
    payload: Payload | None = None,
) -> VectorOperationResponse:
    """Insert or update a vector point in a Qdrant collection."""

    validated = VectorPayload(
        collection=collection,
        id=id,
        vector=vector,
        payload=payload or {},
    )

    try:
        await get_client().upsert(
            collection_name=validated.collection,
            points=[
                models.PointStruct(
                    id=validated.id,
                    vector=validated.vector,
                    payload=validated.payload,
                )
            ],
            wait=True,
        )
    except Exception as exc:
        logger.exception("Failed to upsert vector %s into collection %s.", id, collection)
        raise VectorUpsertError("Failed to upsert vector.") from exc

    return VectorOperationResponse(
        collection=collection,
        id=id,
        status="upserted",
    )


async def search_similar(
    collection: str,
    query_vector: list[float],
    top_k: int = DEFAULT_TOP_K,
    filters: SearchFilters = None,
) -> VectorSearchResponse:
    """Run cosine semantic search against a Qdrant collection."""

    if len(query_vector) != EMBEDDING_DIMENSION:
        raise ValueError(f"query_vector must contain {EMBEDDING_DIMENSION} dimensions.")

    if top_k < 1:
        raise ValueError("top_k must be greater than zero.")

    try:
        search_filter = _build_filter(filters)
        hits = await get_client().search(
            collection_name=collection,
            query_vector=query_vector,
            query_filter=search_filter,
            limit=top_k,
            with_payload=True,
            with_vectors=True,
        )
    except Exception as exc:
        logger.exception("Failed to search collection %s.", collection)
        raise VectorSearchError("Failed to search similar vectors.") from exc

    return VectorSearchResponse(
        collection=collection,
        top_k=top_k,
        results=[
            VectorSearchResult(
                id=hit.id,
                score=float(hit.score),
                payload=dict(hit.payload or {}),
                vector=_extract_vector(getattr(hit, "vector", None)),
            )
            for hit in hits
        ],
    )


async def delete_vector(collection: str, id: VectorId) -> VectorOperationResponse:
    """Delete a vector point from a Qdrant collection by id."""

    try:
        await get_client().delete(
            collection_name=collection,
            points_selector=models.PointIdsList(points=[id]),
            wait=True,
        )
    except Exception as exc:
        logger.exception("Failed to delete vector %s from collection %s.", id, collection)
        raise VectorDeleteError("Failed to delete vector.") from exc

    return VectorOperationResponse(
        collection=collection,
        id=id,
        status="deleted",
    )


async def get_vector(collection: str, id: VectorId) -> VectorGetResponse:
    """Retrieve one vector point from Qdrant by id."""

    try:
        records = await get_client().retrieve(
            collection_name=collection,
            ids=[id],
            with_payload=True,
            with_vectors=True,
        )
    except Exception as exc:
        logger.exception("Failed to retrieve vector %s from collection %s.", id, collection)
        raise VectorGetError("Failed to retrieve vector.") from exc

    if not records:
        return VectorGetResponse(collection=collection, found=False)

    record = records[0]
    return VectorGetResponse(
        collection=collection,
        found=True,
        record=VectorRecord(
            id=record.id,
            payload=dict(record.payload or {}),
            vector=_extract_vector(getattr(record, "vector", None)),
        ),
    )
