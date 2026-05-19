"""Central configuration for the VentureMind AI ML layer.

The ML layer can run as a standalone FastAPI service on ``infra-ml-dev`` and
later merge cleanly with the main application. Configuration is loaded from
environment variables and an optional local ``.env`` file using
``pydantic-settings`` v2.
"""

from __future__ import annotations

from typing import Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class MLConfig(BaseSettings):
    """Runtime settings for ML, vector search, and database infrastructure."""

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
    def validate(self) -> Self:
        """Validate required configuration after environment loading."""

        if not self.database_url.strip():
            raise ValueError("DATABASE_URL must be configured for the ML layer.")

        return self


try:
    ml_config = MLConfig()
except Exception:
    ml_config = None  # type: ignore[assignment]
