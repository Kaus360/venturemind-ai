"""Pydantic v2 contracts for scoring and competitor intelligence.

These models preserve Team Member 1's LangGraph state keys at the request
boundary while exposing ML/infrastructure-friendly response models for FastAPI
routes and downstream agents.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StartupScoreRequest(BaseModel):
    """Input for enhancing Team Member 1's validation response."""

    model_config = ConfigDict(str_strip_whitespace=True)

    startup_id: UUID
    startup_idea: str = Field(min_length=1)
    domain: str = Field(min_length=1, max_length=120)
    innovation_score: float = Field(ge=0.0, le=10.0)
    market_demand: float = Field(ge=0.0, le=10.0)
    competition_risk: float = Field(ge=0.0, le=10.0)
    feasibility: float = Field(ge=0.0, le=10.0)
    weaknesses: list[str] = Field(default_factory=list)

    @field_validator("weaknesses")
    @classmethod
    def clean_weaknesses(cls, weaknesses: list[str]) -> list[str]:
        """Remove blank weakness entries while preserving user wording."""

        return [weakness.strip() for weakness in weaknesses if weakness.strip()]


class StartupScoreResponse(BaseModel):
    """Enhanced startup score response returned by the scoring service."""

    startup_id: UUID
    innovation_score: float
    market_score: float
    competition_score: float
    viability_score: float
    composite_score: float
    grade: str = Field(pattern="^[ABCDF]$")
    summary: str
    recommendations: list[str]


class CompetitorInput(BaseModel):
    """One competitor from Team Member 1's ``CompetitorData`` output."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=255)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)

    @field_validator("strengths", "weaknesses")
    @classmethod
    def clean_items(cls, items: list[str]) -> list[str]:
        """Normalize list fields by dropping empty strings."""

        return [item.strip() for item in items if item.strip()]


class CompetitorAnalysisRequest(BaseModel):
    """Input for enhancing Team Member 1's competitor-data dictionary."""

    model_config = ConfigDict(str_strip_whitespace=True)

    startup_id: UUID
    startup_idea: str = Field(min_length=1)
    domain: str = Field(min_length=1, max_length=120)
    competitors: list[CompetitorInput] = Field(default_factory=list)
    market_gaps: list[str] = Field(default_factory=list)
    opportunity_areas: list[str] = Field(default_factory=list)

    @field_validator("market_gaps", "opportunity_areas")
    @classmethod
    def clean_text_list(cls, items: list[str]) -> list[str]:
        """Normalize list fields by dropping empty strings."""

        return [item.strip() for item in items if item.strip()]


class SimilarCompetitor(BaseModel):
    """A semantically similar competitor retrieved from Qdrant."""

    name: str
    similarity_score: float
    domain: str
    overlap_areas: list[str]


class CompetitorAnalysisResponse(BaseModel):
    """Enhanced competitor intelligence response."""

    startup_id: UUID
    competitor_count: int = Field(ge=0)
    top_competitors: list[str]
    market_gap_score: float = Field(ge=0.0, le=10.0)
    opportunity_score: float = Field(ge=0.0, le=10.0)
    semantic_matches: list[SimilarCompetitor]
    recommendations: list[str]
