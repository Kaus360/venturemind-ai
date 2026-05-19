from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.config import config


@asynccontextmanager
async def lifespan(_: FastAPI):
    Config = type(config)
    Config.validate(config)
    yield


app = FastAPI(
    title="VentureMind AI",
    description="Autonomous Venture Intelligence Platform",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "app": "VentureMind AI"}
