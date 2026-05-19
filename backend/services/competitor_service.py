"""Semantic competitor intelligence service for VentureMind AI.

This module enhances Team Member 1's ``CompetitorData`` output by persisting
competitor records, storing competitor vectors in Qdrant, and retrieving
semantically similar competitors already known to the platform.
"""

from __future__ import annotations

import logging
import os
from typing import Any
from uuid import UUID, uuid5, NAMESPACE_URL

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.schemas import CompetitorAnalysis
from backend.models.scoring_model import (
    CompetitorAnalysisRequest,
    CompetitorAnalysisResponse,
    CompetitorInput,
    SimilarCompetitor,
)
from backend.vectorstore.embedding_pipeline import generate_embedding
from backend.vectorstore.qdrant_client import COMPETITOR_COLLECTION
from backend.vectorstore.vector_search import (
    VectorSearchError,
    VectorUpsertError,
    search_similar,
    upsert_vector,
)

logger = logging.getLogger(__name__)

DEFAULT_COMPETITOR_MATCH_LIMIT = int(os.getenv("COMPETITOR_MATCH_LIMIT", "5"))


class CompetitorServiceError(RuntimeError):
    """Base exception for competitor intelligence failures."""


class CompetitorAnalysisError(CompetitorServiceError):
    """Raised when competitor analysis cannot be completed."""


class CompetitorEmbeddingError(CompetitorServiceError):
    """Raised when competitor embeddings cannot be stored."""


class CompetitorRetrievalError(CompetitorServiceError):
    """Raised when stored competitor analysis cannot be retrieved."""


def _competitor_embedding_id(startup_id: str, competitor_name: str) -> str:
    """Create a deterministic Qdrant point id for competitor vectors."""

    stable_uuid = uuid5(NAMESPACE_URL, f"venturemind:{startup_id}:{competitor_name.lower()}")
    return f"competitor:{stable_uuid}"


def _competitor_description(competitor: CompetitorInput, domain: str) -> str:
    """Build semantic text for a competitor from structured fields."""

    strengths = ", ".join(competitor.strengths) or "not specified"
    weaknesses = ", ".join(competitor.weaknesses) or "not specified"
    return (
        f"Competitor: {competitor.name}\n"
        f"Domain: {domain}\n"
        f"Strengths: {strengths}\n"
        f"Weaknesses: {weaknesses}"
    )


def _score_list_quality(items: list[str], scale: float = 2.0) -> float:
    """Score list richness on a capped 0-10 scale."""

    return round(min(10.0, len(items) * scale), 2)


def _build_recommendations(
    market_gaps: list[str],
    opportunity_areas: list[str],
    competitors: list[CompetitorInput],
) -> list[str]:
    """Generate competitor strategy recommendations."""

    recommendations: list[str] = []

    if market_gaps:
        recommendations.append("Prioritize experiments around the strongest market gaps.")
    if opportunity_areas:
        recommendations.append("Turn opportunity areas into testable positioning hypotheses.")
    if len(competitors) >= 3:
        recommendations.append("Create a differentiation matrix against the top competitors.")
    if not competitors:
        recommendations.append("Expand competitor discovery before making positioning decisions.")
    if not recommendations:
        recommendations.append("Validate competitor assumptions with target-user interviews.")

    return recommendations


def _overlap_areas(payload: dict[str, Any], fallback_domain: str) -> list[str]:
    """Extract overlap areas from a Qdrant competitor payload."""

    overlap = payload.get("overlap_areas")
    if isinstance(overlap, list):
        return [str(item) for item in overlap if str(item).strip()]

    domain = str(payload.get("domain") or fallback_domain).strip()
    return [domain] if domain else []


async def store_competitor_embedding(
    competitor_name: str,
    description: str,
    startup_id: str,
) -> str:
    """Embed and store one competitor in the competitor Qdrant collection."""

    try:
        vector = await generate_embedding(description)
        embedding_id = _competitor_embedding_id(
            startup_id=startup_id,
            competitor_name=competitor_name,
        )
        await upsert_vector(
            collection=COMPETITOR_COLLECTION,
            id=embedding_id,
            vector=vector,
            payload={
                "startup_id": startup_id,
                "competitor_name": competitor_name,
                "description": description,
            },
        )
        return embedding_id
    except (VectorUpsertError, ValueError) as exc:
        logger.exception("Failed to store competitor embedding for %s.", competitor_name)
        raise CompetitorEmbeddingError("Failed to store competitor embedding.") from exc
    except Exception as exc:
        logger.exception("Unexpected competitor embedding failure for %s.", competitor_name)
        raise CompetitorEmbeddingError("Unexpected competitor embedding failure.") from exc


async def analyze_competitors(
    request: CompetitorAnalysisRequest,
    db: AsyncSession,
) -> CompetitorAnalysisResponse:
    """Persist and semantically enrich teammate competitor data."""

    try:
        startup_vector = await generate_embedding(request.startup_idea)
        semantic_response = await search_similar(
            collection=COMPETITOR_COLLECTION,
            query_vector=startup_vector,
            top_k=DEFAULT_COMPETITOR_MATCH_LIMIT,
            filters={"domain": request.domain},
        )
    except (VectorSearchError, ValueError) as exc:
        logger.exception("Failed to search semantic competitor matches.")
        raise CompetitorAnalysisError("Failed to search semantic competitor matches.") from exc

    try:
        for competitor in request.competitors:
            description = _competitor_description(competitor=competitor, domain=request.domain)
            embedding_id = _competitor_embedding_id(
                startup_id=str(request.startup_id),
                competitor_name=competitor.name,
            )

            await upsert_vector(
                collection=COMPETITOR_COLLECTION,
                id=embedding_id,
                vector=await generate_embedding(description),
                payload={
                    "startup_id": str(request.startup_id),
                    "competitor_name": competitor.name,
                    "domain": request.domain,
                    "strengths": competitor.strengths,
                    "weaknesses": competitor.weaknesses,
                    "overlap_areas": request.opportunity_areas or request.market_gaps,
                    "description": description,
                },
            )

            db.add(
                CompetitorAnalysis(
                    startup_id=request.startup_id,
                    competitor_name=competitor.name,
                    strengths={
                        "items": competitor.strengths,
                        "market_gaps": request.market_gaps,
                    },
                    weaknesses={
                        "items": competitor.weaknesses,
                        "opportunity_areas": request.opportunity_areas,
                    },
                    pricing="unknown",
                )
            )

        await db.commit()
    except (SQLAlchemyError, VectorUpsertError, ValueError) as exc:
        await db.rollback()
        logger.exception("Failed to persist competitor analysis for %s.", request.startup_id)
        raise CompetitorAnalysisError("Failed to persist competitor analysis.") from exc
    except Exception as exc:
        await db.rollback()
        logger.exception("Unexpected competitor analysis failure for %s.", request.startup_id)
        raise CompetitorAnalysisError("Unexpected competitor analysis failure.") from exc

    semantic_matches = [
        SimilarCompetitor(
            name=str(match.payload.get("competitor_name") or match.payload.get("name") or "Unknown"),
            similarity_score=round(match.score, 4),
            domain=str(match.payload.get("domain") or request.domain),
            overlap_areas=_overlap_areas(match.payload, fallback_domain=request.domain),
        )
        for match in semantic_response.results
    ]

    return CompetitorAnalysisResponse(
        startup_id=request.startup_id,
        competitor_count=len(request.competitors),
        top_competitors=[competitor.name for competitor in request.competitors[:5]],
        market_gap_score=_score_list_quality(request.market_gaps, scale=2.0),
        opportunity_score=_score_list_quality(request.opportunity_areas, scale=2.5),
        semantic_matches=semantic_matches,
        recommendations=_build_recommendations(
            market_gaps=request.market_gaps,
            opportunity_areas=request.opportunity_areas,
            competitors=request.competitors,
        ),
    )


async def get_competitor_analysis(
    startup_id: str,
    db: AsyncSession,
) -> list[CompetitorAnalysis]:
    """Retrieve stored competitor analysis records for a startup."""

    try:
        parsed_startup_id = UUID(startup_id)
        result = await db.execute(
            select(CompetitorAnalysis)
            .where(CompetitorAnalysis.startup_id == parsed_startup_id)
            .order_by(CompetitorAnalysis.created_at)
        )
        return list(result.scalars().all())
    except (ValueError, SQLAlchemyError) as exc:
        logger.exception("Failed to retrieve competitor analysis for %s.", startup_id)
        raise CompetitorRetrievalError("Failed to retrieve competitor analysis.") from exc
