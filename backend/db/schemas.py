"""Database schema models for VentureMind AI.

This module defines the SQLAlchemy ORM tables owned by the ML and
infrastructure layer. It intentionally imports only ``Base`` from
``backend.db.postgres`` so model registration stays simple and avoids circular
dependencies with services, API routers, or vector-store modules.

Team Member 1 compatibility notes:
- ``startup_idea`` maps to ``Startup.title``.
- ``problem_statement`` maps to ``Startup.description``.
- validation output keys map to ``StartupScore`` fields:
  ``innovation_score``, ``market_demand`` -> ``market_score``,
  ``competition_risk`` -> ``competition_score``, and
  ``feasibility`` -> ``viability_score``.
- competitor-data structures can be persisted in the JSON ``strengths`` and
  ``weaknesses`` columns while scalar pricing remains queryable as text.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.postgres import Base


class User(Base):
    """Registered user of the VentureMind AI platform."""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        """Return a concise debug representation without sensitive data."""

        return f"User(id={self.id!s}, email={self.email!r})"


class Startup(Base):
    """Startup idea profile used for validation and semantic intelligence."""

    __tablename__ = "startups"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    domain: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    target_users: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    competitor_analyses: Mapped[list[CompetitorAnalysis]] = relationship(
        back_populates="startup",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    scores: Mapped[list[StartupScore]] = relationship(
        back_populates="startup",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    embeddings_metadata: Mapped[list[EmbeddingMetadata]] = relationship(
        back_populates="startup",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        """Return a readable representation for logs and debugging."""

        return f"Startup(id={self.id!s}, title={self.title!r}, domain={self.domain!r})"


class CompetitorAnalysis(Base):
    """Competitor analysis record linked to a startup.

    ``strengths`` and ``weaknesses`` are JSON columns so structured teammate
    outputs like competitors, market gaps, opportunity areas, feature maps, or
    bullet lists can be preserved without flattening the analysis too early.
    """

    __tablename__ = "competitor_analysis"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    startup_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("startups.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    competitor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    strengths: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    weaknesses: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    pricing: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    startup: Mapped[Startup] = relationship(back_populates="competitor_analyses")

    def __repr__(self) -> str:
        """Return a concise representation of the competitor analysis row."""

        return (
            "CompetitorAnalysis("
            f"id={self.id!s}, startup_id={self.startup_id!s}, "
            f"competitor_name={self.competitor_name!r})"
        )


class StartupScore(Base):
    """Numerical startup validation scores.

    These columns align with Team Member 1's validation dictionary through the
    service layer mapping: ``market_demand`` maps to ``market_score``,
    ``competition_risk`` maps to ``competition_score``, and ``feasibility``
    maps to ``viability_score``.
    """

    __tablename__ = "startup_scores"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    startup_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("startups.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    innovation_score: Mapped[float] = mapped_column(Float, nullable=False)
    market_score: Mapped[float] = mapped_column(Float, nullable=False)
    competition_score: Mapped[float] = mapped_column(Float, nullable=False)
    viability_score: Mapped[float] = mapped_column(Float, nullable=False)

    startup: Mapped[Startup] = relationship(back_populates="scores")

    def __repr__(self) -> str:
        """Return a compact score summary for diagnostics."""

        return (
            "StartupScore("
            f"id={self.id!s}, startup_id={self.startup_id!s}, "
            f"innovation_score={self.innovation_score!r}, "
            f"viability_score={self.viability_score!r})"
        )


class EmbeddingMetadata(Base):
    """Metadata pointer for startup vectors stored in Qdrant."""

    __tablename__ = "embeddings_metadata"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    startup_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("startups.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    embedding_id: Mapped[str] = mapped_column(String(255), nullable=False)
    vector_db: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    startup: Mapped[Startup] = relationship(back_populates="embeddings_metadata")

    def __repr__(self) -> str:
        """Return the vector metadata identity for logs."""

        return (
            "EmbeddingMetadata("
            f"id={self.id!s}, startup_id={self.startup_id!s}, "
            f"embedding_id={self.embedding_id!r}, vector_db={self.vector_db!r})"
        )
