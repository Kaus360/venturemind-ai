from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "app": "VentureMind AI"}
