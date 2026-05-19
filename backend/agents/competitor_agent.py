from __future__ import annotations

import asyncio
import json
import re
from typing import Any, Dict

from backend.agents.base_agent import BaseAgent


def clean_json(text: str) -> str:
    text = text.strip()
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    return text.strip()


class CompetitorAgent(BaseAgent):
    """Agent responsible for competitor and market-gap analysis."""

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            startup_idea = str(state.get("startup_idea", "")).strip()
            if not startup_idea:
                raise ValueError("Missing required 'startup_idea' in state.")

            system_prompt = (
                "You are VentureMind AI's competitor analysis agent. Analyze existing "
                "competitors for a startup idea, focusing on their strengths, weaknesses, "
                "feature gaps, and poor market positioning. Return a JSON object with "
                "these fields: competitors (list of objects with name, strengths, "
                "weaknesses), market_gaps, opportunity_areas. Return ONLY valid JSON. "
                "No explanation. No markdown."
            )
            user_prompt = (
                f"Startup idea: {startup_idea}\n\n"
                "Analyze the competitive landscape and identify exploitable market gaps. "
                "Return ONLY valid JSON."
            )

            response = await asyncio.to_thread(
                self.llm.invoke,
                self._build_messages(system_prompt, user_prompt),
            )

            content = response.content if hasattr(response, "content") else response
            content = clean_json(content)
            parsed_result = json.loads(content)

            updated_state = dict(state)
            updated_state["competitor_data"] = parsed_result
            updated_state.pop("error", None)
            return updated_state
        except Exception as exc:
            failed_state = dict(state)
            failed_state["competitor_data"] = {}
            failed_state["error"] = f"CompetitorAgent failed: {exc}"
            return failed_state
