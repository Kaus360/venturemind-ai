from __future__ import annotations

from langchain_groq import ChatGroq

from backend.config import get_config


def get_llm_client(*, temperature: float = 0.0, timeout: float | None = 30.0) -> ChatGroq:
    """
    Create a configured Groq chat client for structured agent workflows.

    The default temperature is pinned to 0 to keep JSON outputs predictable.
    """

    config = get_config()
    return ChatGroq(
        api_key=config.groq_api_key.get_secret_value(),
        model=config.groq_model,
        temperature=temperature,
        timeout=timeout,
    )
