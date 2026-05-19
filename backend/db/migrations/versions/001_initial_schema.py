"""Create initial VentureMind AI schema.

Revision ID: 001
Revises: None
Create Date: 2026-05-19
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create all initial application tables and required PostgreSQL extensions."""

    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=False)

    op.create_table(
        "startups",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("domain", sa.String(length=120), nullable=False),
        sa.Column("target_users", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_startups_domain", "startups", ["domain"], unique=False)

    op.create_table(
        "competitor_analysis",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("startup_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("competitor_name", sa.String(length=255), nullable=False),
        sa.Column("strengths", sa.JSON(), nullable=False),
        sa.Column("weaknesses", sa.JSON(), nullable=False),
        sa.Column("pricing", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["startup_id"],
            ["startups.id"],
            name="fk_competitor_analysis_startup_id_startups",
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_competitor_analysis_startup_id",
        "competitor_analysis",
        ["startup_id"],
        unique=False,
    )

    op.create_table(
        "startup_scores",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("startup_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("innovation_score", sa.Float(), nullable=False),
        sa.Column("market_score", sa.Float(), nullable=False),
        sa.Column("competition_score", sa.Float(), nullable=False),
        sa.Column("viability_score", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["startup_id"],
            ["startups.id"],
            name="fk_startup_scores_startup_id_startups",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_startup_scores_startup_id", "startup_scores", ["startup_id"], unique=False)

    op.create_table(
        "embeddings_metadata",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("startup_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("embedding_id", sa.String(length=255), nullable=False),
        sa.Column("vector_db", sa.String(length=80), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["startup_id"],
            ["startups.id"],
            name="fk_embeddings_metadata_startup_id_startups",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "embedding_id",
            "vector_db",
            name="uq_embeddings_metadata_vector",
        ),
    )
    op.create_index(
        "ix_embeddings_metadata_startup_id",
        "embeddings_metadata",
        ["startup_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop all initial application tables in foreign-key-safe order."""

    op.drop_index("ix_embeddings_metadata_startup_id", table_name="embeddings_metadata")
    op.drop_table("embeddings_metadata")

    op.drop_index("ix_startup_scores_startup_id", table_name="startup_scores")
    op.drop_table("startup_scores")

    op.drop_index("ix_competitor_analysis_startup_id", table_name="competitor_analysis")
    op.drop_table("competitor_analysis")

    op.drop_index("ix_startups_domain", table_name="startups")
    op.drop_table("startups")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    op.execute('DROP EXTENSION IF EXISTS "pgcrypto"')
