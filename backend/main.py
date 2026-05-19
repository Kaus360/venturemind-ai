from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ==========================================
# TEAM MEMBER 1 — Agent Orchestration
# ==========================================
from backend.api.routes import router

# ==========================================
# TEAM MEMBER 2 — ML Infrastructure
# ==========================================
from backend.api.ml_routes import router as ml_router
from backend.db.postgres import close_db_connections, verify_connection
from backend.vectorstore.qdrant_client import (
    close_qdrant_client,
    create_collections,
    health_check,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycle events.
    
    Team Member 1 (Agent Orchestration):
      - Config is validated at import time via Config.validate().
      - Note: GROQ_API_KEY must exist in .env.
        
    Team Member 2 (ML Infrastructure):
      - Bootstrap functions are called for Qdrant and PostgreSQL.
      - Gracefully closes connections on shutdown.
    """

    # --- STARTUP: Team Member 2 - ML Infrastructure ---
    try:
        result = await create_collections()
        logger.info("Qdrant collections: %s", result.model_dump())
    except Exception:
        logger.exception("Qdrant init failed.")

    try:
        ok = await verify_connection()
        logger.info("PostgreSQL connected: %s", ok)
    except Exception:
        logger.exception("PostgreSQL init failed.")

    # --- STARTUP: Team Member 1 - Agent Orchestration ---
    # config already validated at import time via Config.validate()
    # GROQ_API_KEY must exist in .env

    yield

    # --- SHUTDOWN: Team Member 2 - ML Infrastructure ---
    try:
        await close_qdrant_client()
        logger.info("Qdrant client closed successfully.")
    except Exception:
        logger.exception("Failed to close Qdrant client.")

    try:
        await close_db_connections()
        logger.info("Database connections closed successfully.")
    except Exception:
        logger.exception("Failed to close Database connections.")


app = FastAPI(
    title="VentureMind AI",
    description="Autonomous Venture Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Team Member 1 router
app.include_router(router, prefix="/api/v1")

# Register Team Member 2 router (already has prefix internally)
app.include_router(ml_router)


@app.get("/health")
async def health_check_endpoint() -> dict[str, Any]:
    """Check overall application health."""
    postgres_ok = False
    qdrant_ok = False

    try:
        postgres_ok = await verify_connection()
    except Exception:
        pass

    try:
        qdrant_status = await health_check()
        qdrant_ok = qdrant_status.is_healthy
    except Exception:
        pass

    overall = "ok" if (postgres_ok and qdrant_ok) else "degraded"

    return {
        "status": overall,
        "app": "VentureMind AI",
        "version": "1.0.0",
        "postgres": postgres_ok,
        "qdrant": qdrant_ok,
        "agent_routes": "/api/v1",
        "ml_routes": "/api/v1/ml",
    }


@app.get("/")
async def root() -> dict[str, Any]:
    """Return API info with both route catalogs."""
    return {
        "app": "VentureMind AI",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "agent_endpoints": [
            "POST /api/v1/generate-problems",
            "POST /api/v1/generate-solution",
            "POST /api/v1/validate-startup",
            "POST /api/v1/analyze-competitors",
            "POST /api/v1/redteam-critique",
            "POST /api/v1/generate-roadmap",
            "POST /api/v1/execute-workflow",
            "GET /api/v1/memory-context",
        ],
        "ml_endpoints": [
            "POST /api/v1/ml/embeddings/startups",
            "POST /api/v1/ml/search/startups",
            "POST /api/v1/ml/scores/startups",
            "GET /api/v1/ml/scores/startups/{startup_id}",
            "POST /api/v1/ml/scores/compare",
            "POST /api/v1/ml/competitors/analyze",
            "GET /api/v1/ml/competitors/{startup_id}",
            "POST /api/v1/ml/retrieval/startups",
            "POST /api/v1/ml/retrieval/competitors",
            "POST /api/v1/ml/retrieval/market-gaps",
            "GET /api/v1/ml/infrastructure/health",
        ],
    }
