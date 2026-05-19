from __future__ import annotations

from fastapi import FastAPI

from backend.config import get_config


config = get_config()

app = FastAPI(
    title="VentureMind AI Backend",
    version="0.1.0",
    docs_url="/docs" if config.app_env != "production" else None,
    redoc_url="/redoc" if config.app_env != "production" else None,
)


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    """Async health endpoint for uptime probes."""

    return {
        "status": "ok",
        "environment": config.app_env,
        "model": config.groq_model,
    }
