"""Pydantic v2 models for startup embedding and similarity search APIs."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StartupEmbedRequest(BaseModel):
    """Request body for embedding and storing a startup profile."""

    model_config = ConfigDict(str_strip_whitespace=True)

    startup_id: UUID
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    domain: str = Field(min_length=1, max_length=120)
    target_users: str = Field(min_length=1)


class StartupEmbedResponse(BaseModel):
    """Response returned after startup embeddings are stored."""

    startup_id: UUID
    embedding_id: str
    vector_db: str
    chunk_count: int = Field(ge=0)
    status: str


class SimilaritySearchRequest(BaseModel):
    """Request body for startup semantic similarity search."""

    model_config = ConfigDict(str_strip_whitespace=True)

    query_text: str = Field(min_length=1)
    top_k: int = Field(default=10, ge=1, le=100)
    domain_filter: str | None = Field(default=None, max_length=120)

    @field_validator("domain_filter")
    @classmethod
    def normalize_domain_filter(cls, value: str | None) -> str | None:
        """Convert blank domain filters into None for simpler search logic."""

        if value is None:
            return None

        stripped = value.strip()
        return stripped or None


class SimilarityResult(BaseModel):
    """One ranked startup similarity result."""

    startup_id: UUID
    title: str
    score: float
    domain: str
    target_users: str


class SimilaritySearchResponse(BaseModel):
    """Response returned by semantic startup search."""

    query_text: str
    results: list[SimilarityResult]
