from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE, override=False)


@dataclass
class Config:
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama3-8b-8192"
    APP_ENV: str = "development"

    @classmethod
    def validate(cls, config: "Config") -> "Config":
        if not config.GROQ_API_KEY or not config.GROQ_API_KEY.strip():
            raise ValueError("GROQ_API_KEY cannot be empty.")
        return config


config = Config.validate(
    Config(
        GROQ_API_KEY=os.getenv("GROQ_API_KEY", ""),
        GROQ_MODEL=os.getenv("GROQ_MODEL", "llama3-8b-8192"),
        APP_ENV=os.getenv("APP_ENV", "development"),
    )
)
