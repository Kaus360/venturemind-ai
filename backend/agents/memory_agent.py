from __future__ import annotations

from typing import Any, Dict

from backend.agents.base_agent import BaseAgent


class MemoryAgent(BaseAgent):
    """Agent responsible for maintaining workflow memory context."""

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            validation = state.get("validation", {})
            critic_feedback = state.get("critic_feedback", {})

            memory_entry = {
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

            updated_state = dict(state)
            memory_context = updated_state.get("memory_context")
            if memory_context is None:
                memory_context = []
            if not isinstance(memory_context, list):
                raise ValueError("memory_context must be a list or None.")

            memory_context.append(memory_entry)
            updated_state["memory_context"] = memory_context
            updated_state.pop("error", None)
            return updated_state
        except Exception as exc:
            failed_state = dict(state)
            failed_state["error"] = f"MemoryAgent failed: {exc}"
            return failed_state
