from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from backend.utils.llm_client import get_llm


class BaseAgent(ABC):
    """Abstract base class for VentureMind AI agents."""

    def __init__(self, temperature: float = 0.7) -> None:
        self.llm = get_llm(temperature=temperature)

    @abstractmethod
    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent and return a structured JSON-compatible dict."""

    def _build_messages(self, system_prompt: str, user_prompt: str) -> list[tuple[str, str]]:
        return [
            ("system", system_prompt),
            ("user", user_prompt),
        ]
