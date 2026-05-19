"""Standalone FastAPI application for the VentureMind AI ML layer.

This app is intentionally separate from Team Member 1's ``main.py`` and router.
It can be launched independently during ML-layer development, while all routes
remain under ``/api/v1/ml`` through ``backend.api.ml_routes``.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.ml_routes import router as ml_router
from backend.db.postgres import close_db_connections, verify_connection
from backend.vectorstore.qdrant_client import (
    close_qdrant_client,
    create_collections,
    health_check,
)

logger = logging.getLogger(__name__)

APP_NAME = "VentureMind AI — ML Intelligence Layer"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize and clean up ML infrastructure for the standalone app."""

    try:
        collection_result = await create_collections()
        logger.info("Qdrant collections ready: %s", collection_result.model_dump())
    except Exception:
        logger.exception("Failed to initialize Qdrant collections during startup.")

    try:
        postgres_status = await verify_connection()
        logger.info("PostgreSQL startup health status: %s", postgres_status)
    except Exception:
        logger.exception("Failed to verify PostgreSQL connection during startup.")

    yield

    try:
        await close_qdrant_client()
        logger.info("Qdrant client closed.")
    except Exception:
        logger.exception("Failed to close Qdrant client during shutdown.")

    try:
        await close_db_connections()
        logger.info("PostgreSQL connections closed.")
    except Exception:
        logger.exception("Failed to close PostgreSQL connections during shutdown.")


app = FastAPI(
    title=APP_NAME,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ml_router)


@app.get("/health")
async def health() -> dict[str, Any]:
    """Return health status for the standalone ML application."""

    postgres_ok = False
    postgres_payload: dict[str, Any] = {"is_healthy": False}
    qdrant_payload: dict[str, Any] = {"is_healthy": False}

    try:
        postgres_ok = await verify_connection()
        postgres_payload = {"is_healthy": postgres_ok}
    except Exception as exc:
        postgres_payload = {"is_healthy": False, "error": str(exc)}
        logger.exception("PostgreSQL health check failed.")

    try:
        qdrant_status = await health_check()
        qdrant_payload = qdrant_status.model_dump()
    except Exception as exc:
        qdrant_payload = {"is_healthy": False, "error": str(exc)}
        logger.exception("Qdrant health check failed.")

    status = "ok" if postgres_ok and qdrant_payload.get("is_healthy") else "degraded"

    return {
        "status": status,
        "app": APP_NAME,
        "postgres": postgres_payload,
        "qdrant": qdrant_payload,
    }


@app.get("/")
async def root() -> dict[str, Any]:
    """Return API metadata and the ML endpoint catalog."""

    return {
        "app": APP_NAME,
        "status": "running",
        "base_path": "/api/v1/ml",
        "docs": "/docs",
        "health": "/health",
        "endpoints": [
            "POST /api/v1/ml/embeddings/startups",
            "POST /api/v1/ml/search/startups",
            "DELETE /api/v1/ml/embeddings/startups/{startup_id}",
            "POST /api/v1/ml/scores/startups",
            "GET /api/v1/ml/scores/startups/{startup_id}",
            "POST /api/v1/ml/scores/compare",
            "POST /api/v1/ml/competitors/analyze",
            "GET /api/v1/ml/competitors/{startup_id}",
            "POST /api/v1/ml/retrieval/startups",
            "POST /api/v1/ml/retrieval/competitors",
            "POST /api/v1/ml/retrieval/market-gaps",
            "POST /api/v1/ml/infrastructure/bootstrap",
            "GET /api/v1/ml/infrastructure/health",
            "POST /api/v1/ml/infrastructure/shutdown?confirm=true",
        ],
    }
