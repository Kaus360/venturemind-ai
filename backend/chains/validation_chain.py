from __future__ import annotations

import asyncio
from typing import Any

from backend.agents.validation_agent import ValidationAgent


class ValidationChain:
    """Retry wrapper for validation agent execution."""

    @staticmethod
    def _has_valid_scores(result: dict[str, Any]) -> bool:
        validation = result.get("validation", {})
        if not isinstance(validation, dict):
            return False

        score_keys = (
            "innovation_score",
            "market_demand",
            "competition_risk",
            "feasibility",
        )

        scores: list[float] = []
        for key in score_keys:
            value = validation.get(key)
            if not isinstance(value, (int, float)):
                return False
            scores.append(float(value))

        return all(score > 0 for score in scores)

    async def run_with_retry(self, state: dict[str, Any], max_retries: int = 3) -> dict[str, Any]:
        agent = ValidationAgent()
        last_result: dict[str, Any] = dict(state)

        for attempt in range(max_retries):
            last_result = await agent.run(state)
            if self._has_valid_scores(last_result):
                return last_result

            if attempt < max_retries - 1:
                await asyncio.sleep(1)

        exhausted_result = dict(last_result)
        exhausted_result["retry_exhausted"] = True
        return exhausted_result
