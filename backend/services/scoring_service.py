"""ML-assisted startup scoring service for VentureMind AI.

The functions here accept Team Member 1's validation scores, compute an
investor-friendly composite score, persist the raw mapped dimensions to
PostgreSQL, and return enriched recommendations for the LangGraph state.
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
from backend.models.scoring_model import StartupScoreRequest, StartupScoreResponse

logger = logging.getLogger(__name__)


class ScoringServiceError(RuntimeError):
    """Base exception for startup scoring failures."""


class ScoreComputationError(ScoringServiceError):
    """Raised when a score cannot be computed or persisted."""


class ScoreRetrievalError(ScoringServiceError):
    """Raised when stored startup scores cannot be retrieved."""


class ScoreComparisonError(ScoringServiceError):
    """Raised when two startups cannot be compared."""


def _competition_strength_from_risk(competition_risk: float) -> float:
    """Invert competition risk so higher values mean a stronger opportunity."""

    return max(0.0, min(10.0, 10.0 - competition_risk))


def _compute_composite_score(
    innovation_score: float,
    market_score: float,
    competition_score: float,
    viability_score: float,
) -> float:
    """Compute the weighted composite score on a 0-10 scale."""

    return round(
        (innovation_score * 0.30)
        + (market_score * 0.25)
        + (competition_score * 0.20)
        + (viability_score * 0.25),
        2,
    )


def _assign_grade(composite_score: float) -> str:
    """Translate a composite score into an A/B/C/D/F grade."""

    if composite_score >= 8.5:
        return "A"
    if composite_score >= 7.0:
        return "B"
    if composite_score >= 5.5:
        return "C"
    if composite_score >= 4.0:
        return "D"
    return "F"


def _build_recommendations(
    innovation_score: float,
    market_score: float,
    competition_score: float,
    viability_score: float,
    weaknesses: list[str] | None = None,
) -> list[str]:
    """Generate practical recommendations based on weak dimensions."""

    recommendations: list[str] = []

    if innovation_score < 6.0:
        recommendations.append("Sharpen the unique insight, technical moat, or workflow advantage.")
    if market_score < 6.0:
        recommendations.append("Validate urgency with target-user interviews and demand signals.")
    if competition_score < 6.0:
        recommendations.append("Clarify differentiation against incumbents and substitute solutions.")
    if viability_score < 6.0:
        recommendations.append("Reduce execution risk with a narrower MVP and measurable milestones.")

    for weakness in weaknesses or []:
        recommendations.append(f"Address validation weakness: {weakness}")

    if not recommendations:
        recommendations.append("Proceed to deeper customer discovery and MVP scoping.")

    return recommendations


def _build_summary(composite_score: float, grade: str) -> str:
    """Create a concise score summary for API responses."""

    return f"Composite score {composite_score:.2f}/10 with grade {grade}."


def _response_from_scores(
    startup_id: UUID,
    innovation_score: float,
    market_score: float,
    competition_score: float,
    viability_score: float,
    weaknesses: list[str] | None = None,
) -> StartupScoreResponse:
    """Build the public response model from normalized score dimensions."""

    composite_score = _compute_composite_score(
        innovation_score=innovation_score,
        market_score=market_score,
        competition_score=competition_score,
        viability_score=viability_score,
    )
    grade = _assign_grade(composite_score)

    return StartupScoreResponse(
        startup_id=startup_id,
        innovation_score=round(innovation_score, 2),
        market_score=round(market_score, 2),
        competition_score=round(competition_score, 2),
        viability_score=round(viability_score, 2),
        composite_score=composite_score,
        grade=grade,
        summary=_build_summary(composite_score=composite_score, grade=grade),
        recommendations=_build_recommendations(
            innovation_score=innovation_score,
            market_score=market_score,
            competition_score=competition_score,
            viability_score=viability_score,
            weaknesses=weaknesses,
        ),
    )


async def compute_startup_score(
    request: StartupScoreRequest,
    db: AsyncSession,
) -> StartupScoreResponse:
    """Compute, persist, and return an enhanced startup score.

    ``competition_risk`` from Team Member 1 is inverted before persistence so
    ``competition_score`` follows the platform convention that higher is better.
    """

    competition_score = _competition_strength_from_risk(request.competition_risk)
    response = _response_from_scores(
        startup_id=request.startup_id,
        innovation_score=request.innovation_score,
        market_score=request.market_demand,
        competition_score=competition_score,
        viability_score=request.feasibility,
        weaknesses=request.weaknesses,
    )

    try:
        db.add(
            StartupScore(
                startup_id=request.startup_id,
                innovation_score=response.innovation_score,
                market_score=response.market_score,
                competition_score=response.competition_score,
                viability_score=response.viability_score,
            )
        )
        await db.commit()
        return response
    except SQLAlchemyError as exc:
        await db.rollback()
        logger.exception("Failed to persist startup score for %s.", request.startup_id)
        raise ScoreComputationError("Failed to persist startup score.") from exc
    except Exception as exc:
        await db.rollback()
        logger.exception("Unexpected scoring failure for %s.", request.startup_id)
        raise ScoreComputationError("Unexpected startup scoring failure.") from exc


async def get_startup_scores(
    startup_id: str,
    db: AsyncSession,
) -> list[StartupScoreResponse]:
    """Retrieve all stored scores for a startup."""

    try:
        parsed_startup_id = UUID(startup_id)
        result = await db.execute(
            select(StartupScore)
            .where(StartupScore.startup_id == parsed_startup_id)
            .order_by(StartupScore.id)
        )
        scores = result.scalars().all()
    except (ValueError, SQLAlchemyError) as exc:
        logger.exception("Failed to retrieve startup scores for %s.", startup_id)
        raise ScoreRetrievalError("Failed to retrieve startup scores.") from exc

    return [
        _response_from_scores(
            startup_id=score.startup_id,
            innovation_score=score.innovation_score,
            market_score=score.market_score,
            competition_score=score.competition_score,
            viability_score=score.viability_score,
        )
        for score in scores
    ]


def _average_response(startup_id: UUID, scores: list[StartupScoreResponse]) -> dict[str, Any]:
    """Summarize a startup's score history for comparison output."""

    if not scores:
        return {
            "startup_id": str(startup_id),
            "score_count": 0,
            "average_composite_score": None,
            "latest_grade": None,
        }

    return {
        "startup_id": str(startup_id),
        "score_count": len(scores),
        "average_composite_score": round(mean(score.composite_score for score in scores), 2),
        "latest_grade": scores[-1].grade,
        "latest_composite_score": scores[-1].composite_score,
    }


async def compare_startup_scores(
    startup_id_a: str,
    startup_id_b: str,
    db: AsyncSession,
) -> dict[str, Any]:
    """Compare two startups by stored composite scores."""

    try:
        parsed_a = UUID(startup_id_a)
        parsed_b = UUID(startup_id_b)
        scores_a = await get_startup_scores(startup_id_a=startup_id_a, db=db)
        scores_b = await get_startup_scores(startup_id_b, db=db)

        summary_a = _average_response(parsed_a, scores_a)
        summary_b = _average_response(parsed_b, scores_b)

        score_a = summary_a.get("average_composite_score")
        score_b = summary_b.get("average_composite_score")
        winner: str | None
        difference: float | None

        if score_a is None or score_b is None:
            winner = None
            difference = None
        elif score_a > score_b:
            winner = startup_id_a
            difference = round(score_a - score_b, 2)
        elif score_b > score_a:
            winner = startup_id_b
            difference = round(score_b - score_a, 2)
        else:
            winner = "tie"
            difference = 0.0

        return {
            "startup_a": summary_a,
            "startup_b": summary_b,
            "winner": winner,
            "difference": difference,
        }
    except (ValueError, ScoreRetrievalError) as exc:
        logger.exception("Failed to compare startup scores.")
        raise ScoreComparisonError("Failed to compare startup scores.") from exc
