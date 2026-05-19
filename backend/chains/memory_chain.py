from __future__ import annotations

from typing import Any


class MemoryChain:
    """In-memory chain for storing summarized workflow context."""

    def __init__(self) -> None:
        self.conversation_history: list[dict[str, Any]] = []

    def add_entry(self, state: dict[str, Any]) -> None:
        validation = state.get("validation", {})
        critic_feedback = state.get("critic_feedback", {})

        entry = {
            "domain": state.get("domain"),
            "problem_statement": state.get("problem_statement"),
            "startup_idea": state.get("startup_idea"),
            "validation_scores": {
                "innovation_score": validation.get("innovation_score"),
                "market_demand": validation.get("market_demand"),
                "competition_risk": validation.get("competition_risk"),
                "feasibility": validation.get("feasibility"),
            },
            "verdict": critic_feedback.get("verdict"),
        }
        self.conversation_history.append(entry)

    def get_context(self) -> list[dict[str, Any]]:
        return self.conversation_history

    def get_last_entry(self) -> dict[str, Any]:
        if not self.conversation_history:
            return {}
        return self.conversation_history[-1]

    def clear(self) -> None:
        self.conversation_history.clear()


memory_chain = MemoryChain()
