from __future__ import annotations

from functools import lru_cache
from os import getenv
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field, SecretStr, ValidationError, field_validator


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE, override=False)


class Config(BaseModel):
    """Application configuration loaded from environment variables."""

    groq_api_key: SecretStr = Field(...)
    groq_model: str = Field(default="llama3-8b-8192")
    app_env: str = Field(default="development")

    @field_validator("groq_model")
    @classmethod
    def validate_groq_model(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("GROQ_MODEL cannot be empty.")
        return normalized

    @field_validator("app_env")
    @classmethod
    def validate_app_env(cls, value: str) -> str:
        normalized = value.strip().lower()
        allowed = {"development", "staging", "production", "test"}
        if normalized not in allowed:
            raise ValueError(f"APP_ENV must be one of: {', '.join(sorted(allowed))}.")
        return normalized


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Return a cached, validated application config instance."""

    try:
        return Config(
            groq_api_key=getenv("GROQ_API_KEY"),
            groq_model=getenv("GROQ_MODEL", "llama3-8b-8192"),
            app_env=getenv("APP_ENV", "development"),
        )
    except ValidationError as exc:
        raise RuntimeError(f"Invalid application configuration: {exc}") from exc
