from __future__ import annotations

from langchain_groq import ChatGroq

from backend.config import config


def get_llm(*, temperature: float = 0.7, model: str | None = None) -> ChatGroq:
    """Return a configured Groq chat model instance."""

    return ChatGroq(
        groq_api_key=config.GROQ_API_KEY,
        model_name=model or config.GROQ_MODEL,
        temperature=temperature,
    )
