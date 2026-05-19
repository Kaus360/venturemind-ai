from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel

from backend.utils.llm_client import get_llm_client


AgentState = dict[str, Any]


class BaseAgent(ABC):
    """
    Shared contract for all backend agents.

    Agents must accept a mutable state dictionary and return a JSON-serializable
    state dictionary so they compose cleanly in LangGraph workflows.
    """

    def __init__(self, *, llm: BaseChatModel | None = None) -> None:
        self.llm = llm or get_llm_client()

    @abstractmethod
    async def run(self, state: AgentState) -> AgentState:
        """
        Execute agent logic asynchronously.

        Implementations must return a structured JSON-compatible dictionary.
        """

    def validate_state(self, state: AgentState) -> AgentState:
        if not isinstance(state, dict):
            raise TypeError("Agent state must be a dictionary.")
        return state

    def ensure_json_response(self, payload: Any) -> AgentState:
        if not isinstance(payload, dict):
            raise TypeError("Agents must return a structured JSON object as a dictionary.")
        return payload
