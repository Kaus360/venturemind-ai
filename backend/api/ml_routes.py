"""FastAPI routes for VentureMind AI ML and infrastructure services.

The router is intentionally namespaced under ``/api/v1/ml`` so it can run next
to Team Member 1's LangGraph endpoints without path collisions while sharing
the same base URL and request/response contracts.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.postgres import close_db_connections, get_db, verify_connection
from backend.models.embedding_model import (
    SimilaritySearchRequest,
    SimilaritySearchResponse,
    StartupEmbedRequest,
    StartupEmbedResponse,
)
from backend.models.scoring_model import (
    CompetitorAnalysisRequest,
    CompetitorAnalysisResponse,
    StartupScoreRequest,
    StartupScoreResponse,
)
from backend.services.competitor_service import (
    CompetitorServiceError,
    analyze_competitors,
    get_competitor_analysis,
)
from backend.services.retrieval_service import (
    RetrievalServiceError,
    retrieve_competitors,
    retrieve_market_gaps,
    retrieve_startups,
)
from backend.services.scoring_service import (
    ScoringServiceError,
    compare_startup_scores,
    compute_startup_score,
    get_startup_scores,
)
from backend.services.semantic_service import (
    SemanticServiceError,
    delete_startup_embeddings,
    embed_and_store_startup,
    search_similar_startups,
)
from backend.vectorstore.qdrant_client import (
    close_qdrant_client,
    create_collections,
    health_check,
)

router = APIRouter(prefix="/api/v1/ml", tags=["ML Intelligence"])


class StartupRetrievalRequest(BaseModel):
    """Request body for hybrid startup retrieval."""

    model_config = ConfigDict(str_strip_whitespace=True)

    query: str = Field(min_length=1)
    domain: str | None = Field(default=None, max_length=120)
    top_k: int = Field(default=10, ge=1, le=100)


class CompetitorRetrievalRequest(BaseModel):
    """Request body for semantic competitor retrieval."""

    model_config = ConfigDict(str_strip_whitespace=True)

    startup_idea: str = Field(min_length=1)
    domain: str | None = Field(default=None, max_length=120)
    top_k: int = Field(default=10, ge=1, le=100)


class MarketGapRetrievalRequest(BaseModel):
    """Request body for market-gap retrieval."""

    model_config = ConfigDict(str_strip_whitespace=True)

    domain: str = Field(min_length=1, max_length=120)
    top_k: int = Field(default=10, ge=1, le=100)


class ScoreComparisonRequest(BaseModel):
    """Request body for comparing two startup score histories."""

    startup_id_a: str = Field(min_length=1)
    startup_id_b: str = Field(min_length=1)


def _raise_service_error(exc: Exception) -> None:
    """Translate service exceptions into consistent HTTP 500 responses."""

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=str(exc),
    ) from exc


@router.post("/embeddings/startups", response_model=StartupEmbedResponse)
async def create_startup_embedding(
    request: StartupEmbedRequest,
    db: AsyncSession = Depends(get_db),
) -> StartupEmbedResponse:
    """Embed a startup profile and store vectors plus metadata."""

    try:
        return await embed_and_store_startup(request=request, db=db)
    except SemanticServiceError as exc:
        _raise_service_error(exc)


@router.post("/search/startups", response_model=SimilaritySearchResponse)
async def search_startups(request: SimilaritySearchRequest) -> SimilaritySearchResponse:
    """Run semantic startup similarity search."""

    try:
        return await search_similar_startups(request=request)
    except SemanticServiceError as exc:
        _raise_service_error(exc)


@router.delete("/embeddings/startups/{startup_id}")
async def remove_startup_embeddings(startup_id: str) -> dict[str, Any]:
    """Delete all vector embeddings and metadata for a startup."""

    try:
        return await delete_startup_embeddings(startup_id=startup_id)
    except SemanticServiceError as exc:
        _raise_service_error(exc)


@router.post("/scores/startups", response_model=StartupScoreResponse)
async def score_startup(
    request: StartupScoreRequest,
    db: AsyncSession = Depends(get_db),
) -> StartupScoreResponse:
    """Compute and persist enhanced startup scoring."""

    try:
        return await compute_startup_score(request=request, db=db)
    except ScoringServiceError as exc:
        _raise_service_error(exc)


@router.get("/scores/startups/{startup_id}", response_model=list[StartupScoreResponse])
async def list_startup_scores(
    startup_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[StartupScoreResponse]:
    """List all stored scores for a startup."""

    try:
        return await get_startup_scores(startup_id=startup_id, db=db)
    except ScoringServiceError as exc:
        _raise_service_error(exc)


@router.post("/scores/compare")
async def compare_scores(
    request: ScoreComparisonRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Compare score histories for two startups."""

    try:
        return await compare_startup_scores(
            startup_id_a=request.startup_id_a,
            startup_id_b=request.startup_id_b,
            db=db,
        )
    except ScoringServiceError as exc:
        _raise_service_error(exc)


@router.post("/competitors/analyze", response_model=CompetitorAnalysisResponse)
async def analyze_competitor_data(
    request: CompetitorAnalysisRequest,
    db: AsyncSession = Depends(get_db),
) -> CompetitorAnalysisResponse:
    """Enhance Team Member 1 competitor data with semantic intelligence."""

    try:
        return await analyze_competitors(request=request, db=db)
    except CompetitorServiceError as exc:
        _raise_service_error(exc)


@router.get("/competitors/{startup_id}")
async def list_competitor_analysis(
    startup_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return stored competitor-analysis rows for a startup."""

    try:
        records = await get_competitor_analysis(startup_id=startup_id, db=db)
        return [
            {
                "id": str(record.id),
                "startup_id": str(record.startup_id),
                "competitor_name": record.competitor_name,
                "strengths": record.strengths,
                "weaknesses": record.weaknesses,
                "pricing": record.pricing,
                "created_at": record.created_at.isoformat(),
            }
            for record in records
        ]
    except CompetitorServiceError as exc:
        _raise_service_error(exc)


@router.post("/retrieval/startups")
async def hybrid_startup_retrieval(
    request: StartupRetrievalRequest,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Retrieve startups by semantic relevance plus relational scoring context."""

    try:
        return await retrieve_startups(
            query=request.query,
            domain=request.domain,
            top_k=request.top_k,
            db=db,
        )
    except RetrievalServiceError as exc:
        _raise_service_error(exc)


@router.post("/retrieval/competitors")
async def hybrid_competitor_retrieval(
    request: CompetitorRetrievalRequest,
) -> list[dict[str, Any]]:
    """Retrieve semantically similar competitors from the vector index."""

    try:
        return await retrieve_competitors(
            startup_idea=request.startup_idea,
            domain=request.domain,
            top_k=request.top_k,
        )
    except RetrievalServiceError as exc:
        _raise_service_error(exc)


@router.post("/retrieval/market-gaps")
async def hybrid_market_gap_retrieval(
    request: MarketGapRetrievalRequest,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Retrieve low-competition market-gap opportunities for a domain."""

    try:
        return await retrieve_market_gaps(
            domain=request.domain,
            top_k=request.top_k,
            db=db,
        )
    except RetrievalServiceError as exc:
        _raise_service_error(exc)


@router.post("/infrastructure/bootstrap")
async def bootstrap_ml_infrastructure() -> dict[str, Any]:
    """Create required vector collections for ML services."""

    try:
        result = await create_collections()
        return result.model_dump()
    except Exception as exc:
        _raise_service_error(exc)


@router.get("/infrastructure/health")
async def ml_health_check() -> dict[str, Any]:
    """Check PostgreSQL and Qdrant health for the ML layer."""

    try:
        postgres_ok = await verify_connection()
        qdrant_status = await health_check()
        return {
            "postgres": {"is_healthy": postgres_ok},
            "qdrant": qdrant_status.model_dump(),
        }
    except Exception as exc:
        _raise_service_error(exc)


@router.post("/infrastructure/shutdown")
async def shutdown_ml_infrastructure(
    confirm: bool = Query(default=False),
) -> dict[str, str]:
    """Close DB and Qdrant clients when explicitly requested by operators."""

    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Set confirm=true to close infrastructure clients.",
        )

    try:
        await close_qdrant_client()
        await close_db_connections()
        return {"status": "closed"}
    except Exception as exc:
        _raise_service_error(exc)
