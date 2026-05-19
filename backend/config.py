from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from dotenv import load_dotenv
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"
load_dotenv(ENV_FILE, override=False)


# --- Team Member 1: Agent Orchestration Config ---
@dataclass
class Config:
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    APP_ENV: str = "development"

    @classmethod
    def validate(cls, config: "Config") -> "Config":
        if not config.GROQ_API_KEY or not config.GROQ_API_KEY.strip():
            raise ValueError("GROQ_API_KEY cannot be empty.")
        return config


config = Config.validate(
    Config(
        GROQ_API_KEY=os.getenv("GROQ_API_KEY", ""),
        GROQ_MODEL=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        APP_ENV=os.getenv("APP_ENV", "development"),
    )
)


# --- Team Member 2: ML Infrastructure Config ---
class MLConfig(BaseSettings):
    database_url: str = ""
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_vector_size: int = 384
    qdrant_startup_collection: str = "startup_embeddings"
    qdrant_competitor_collection: str = "competitor_embeddings"
    huggingface_api_key: str = ""
    groq_api_key: str = ""
    db_pool_size: int = 5
    db_max_overflow: int = 10
    sqlalchemy_echo: bool = False
    vector_search_default_top_k: int = 10
    competitor_match_limit: int = 5
    text_chunk_size: int = 800
    text_chunk_overlap: int = 120
    environment: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @model_validator(mode="after")
    def validate_ml(self) -> Self:
        return self


try:
    ml_config = MLConfig()
except Exception:
    ml_config = None
