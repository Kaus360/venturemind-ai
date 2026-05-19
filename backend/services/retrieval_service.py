"""Hybrid retrieval services for VentureMind AI.

The retrieval layer combines semantic vector search from Qdrant with relational
signals from PostgreSQL. It is designed for API routes and agents that need
ranked startup, competitor, or market-gap context without knowing the storage
details behind those signals.
"""

from __future__ import annotations

import logging
from statistics import mean
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.schemas import StartupScore
from backend.vectorstore.embedding_pipeline import generate_embedding
from backend.vectorstore.qdrant_client import COMPETITOR_COLLECTION, STARTUP_COLLECTION
from backend.vectorstore.vector_search import VectorSearchError, search_similar

logger = logging.getLogger(__name__)


class RetrievalServiceError(RuntimeError):
    """Base exception for retrieval-service failures."""


class StartupRetrievalError(RetrievalServiceError):
    """Raised when startup retrieval fails."""


class CompetitorRetrievalError(RetrievalServiceError):
    """Raised when competitor retrieval fails."""


class MarketGapRetrievalError(RetrievalServiceError):
    """Raised when market-gap retrieval fails."""


def _score_payload(score: StartupScore) -> dict[str, float]:
    """Serialize a stored ``StartupScore`` into API-safe numeric fields."""

    composite_score = round(
        (score.innovation_score * 0.30)
        + (score.market_score * 0.25)
        + (score.competition_score * 0.20)
        + (score.viability_score * 0.25),
        2,
    )

    return {
        "innovation_score": round(score.innovation_score, 2),
        "market_score": round(score.market_score, 2),
        "competition_score": round(score.competition_score, 2),
        "viability_score": round(score.viability_score, 2),
        "composite_score": composite_score,
    }


async def _fetch_latest_scores(
    startup_ids: list[str],
    db: AsyncSession,
) -> dict[str, dict[str, float]]:
    """Fetch the latest score row for each startup id in a result set."""

    parsed_ids: list[UUID] = []
    for startup_id in startup_ids:
        try:
            parsed_ids.append(UUID(startup_id))
        except ValueError:
            logger.warning("Skipping malformed startup_id from vector payload: %s", startup_id)

    if not parsed_ids:
        return {}

    result = await db.execute(
        select(StartupScore)
        .where(StartupScore.startup_id.in_(parsed_ids))
        .order_by(StartupScore.startup_id, StartupScore.id)
    )

    latest_scores: dict[str, dict[str, float]] = {}
    for score in result.scalars().all():
        latest_scores[str(score.startup_id)] = _score_payload(score)

    return latest_scores


async def retrieve_startups(
    query: str,
    domain: str | None,
    top_k: int,
    db: AsyncSession,
) -> list[dict[str, Any]]:
    """Retrieve semantically similar startups enriched with PostgreSQL scores."""

    try:
        query_vector = await generate_embedding(query)
        filters = {"domain": domain} if domain else None
        vector_results = await search_similar(
            collection=STARTUP_COLLECTION,
            query_vector=query_vector,
            top_k=top_k,
            filters=filters,
        )

        startup_ids = [
            str(match.payload["startup_id"])
            for match in vector_results.results
            if match.payload.get("startup_id")
        ]
        scores_by_startup = await _fetch_latest_scores(startup_ids=startup_ids, db=db)
    except (VectorSearchError, SQLAlchemyError, ValueError) as exc:
        logger.exception("Failed to retrieve startups for query=%r.", query)
        raise StartupRetrievalError("Failed to retrieve startups.") from exc

    ranked_results: list[dict[str, Any]] = []
    seen: set[str] = set()

    for rank, match in enumerate(vector_results.results, start=1):
        payload = match.payload
        startup_id = str(payload.get("startup_id", ""))

        if not startup_id or startup_id in seen:
            continue

        ranked_results.append(
            {
                "rank": rank,
                "startup_id": startup_id,
                "title": payload.get("title"),
                "domain": payload.get("domain"),
                "target_users": payload.get("target_users"),
                "semantic_score": round(match.score, 4),
                "scores": scores_by_startup.get(startup_id),
                "payload": payload,
            }
        )
        seen.add(startup_id)

    return ranked_results


async def retrieve_competitors(
    startup_idea: str,
    domain: str | None,
    top_k: int,
) -> list[dict[str, Any]]:
    """Retrieve semantically similar competitors from Qdrant."""

    try:
        query_vector = await generate_embedding(startup_idea)
        filters = {"domain": domain} if domain else None
        vector_results = await search_similar(
            collection=COMPETITOR_COLLECTION,
            query_vector=query_vector,
            top_k=top_k,
            filters=filters,
        )
    except (VectorSearchError, ValueError) as exc:
        logger.exception("Failed to retrieve competitors for domain=%r.", domain)
        raise CompetitorRetrievalError("Failed to retrieve competitors.") from exc

    return [
        {
            "rank": rank,
            "competitor_name": match.payload.get("competitor_name") or match.payload.get("name"),
            "domain": match.payload.get("domain"),
            "similarity_score": round(match.score, 4),
            "payload": match.payload,
        }
        for rank, match in enumerate(vector_results.results, start=1)
    ]


async def retrieve_market_gaps(
    domain: str,
    top_k: int,
    db: AsyncSession,
) -> list[dict[str, Any]]:
    """Identify possible underserved niches from low-competition startup areas."""

    try:
        query_vector = await generate_embedding(f"underserved market gaps and opportunities in {domain}")
        vector_results = await search_similar(
            collection=STARTUP_COLLECTION,
            query_vector=query_vector,
            top_k=top_k,
            filters={"domain": domain},
        )

        startup_ids = [
            str(match.payload["startup_id"])
            for match in vector_results.results
            if match.payload.get("startup_id")
        ]
        scores_by_startup = await _fetch_latest_scores(startup_ids=startup_ids, db=db)
    except (VectorSearchError, SQLAlchemyError, ValueError) as exc:
        logger.exception("Failed to retrieve market gaps for domain=%r.", domain)
        raise MarketGapRetrievalError("Failed to retrieve market gaps.") from exc

    opportunities: list[dict[str, Any]] = []
    for match in vector_results.results:
        payload = match.payload
        startup_id = str(payload.get("startup_id", ""))
        scores = scores_by_startup.get(startup_id) or {}
        competition_score = scores.get("competition_score")

        # ``competition_score`` is Team Member 1's competition_risk after
        # inversion, so higher values mean lower competitive pressure.
        if competition_score is not None and competition_score < 6.0:
            continue

        niche_signals = [
            str(item)
            for item in [
                payload.get("title"),
                payload.get("target_users"),
                payload.get("chunk"),
            ]
            if item
        ]

        opportunities.append(
            {
                "startup_id": startup_id,
                "domain": domain,
                "opportunity": payload.get("title") or f"Underserved niche in {domain}",
                "semantic_score": round(match.score, 4),
                "competition_score": competition_score,
                "confidence": round(mean([match.score, (competition_score or 5.0) / 10.0]), 4),
                "signals": niche_signals[:3],
                "payload": payload,
            }
        )

    return opportunities[:top_k]
