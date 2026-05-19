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


class RoadmapAgent(BaseAgent):
    """Agent responsible for generating a structured startup roadmap."""

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            startup_idea = str(state.get("startup_idea", "")).strip()
            solution = state.get("solution", {})
            validation = state.get("validation", {})

            if not startup_idea:
                raise ValueError("Missing required 'startup_idea' in state.")
            if not solution:
                raise ValueError("Missing required 'solution' in state.")
            if not validation:
                raise ValueError("Missing required 'validation' in state.")

            system_prompt = (
                "You are VentureMind AI's roadmap planning agent. Generate a structured "
                "startup execution roadmap based on the startup idea, proposed solution, "
                "and validation context. Return a JSON object with these fields: "
                "mvp_features, phase_1, phase_2, phase_3, scaling_strategy. Each phase "
                "must be an object with timeline and goals. Return ONLY valid JSON. "
                "No explanation. No markdown."
            )
            user_prompt = (
                f"Startup idea: {startup_idea}\n\n"
                f"Solution context: {json.dumps(solution)}\n\n"
                f"Validation context: {json.dumps(validation)}\n\n"
                "Generate a structured startup roadmap with MVP priorities, phased goals, "
                "and a scaling strategy. Return ONLY valid JSON."
            )

            response = await asyncio.to_thread(
                self.llm.invoke,
                self._build_messages(system_prompt, user_prompt),
            )

            content = response.content if hasattr(response, "content") else response
            content = clean_json(content)
            parsed_result = json.loads(content)

            updated_state = dict(state)
            updated_state["roadmap"] = parsed_result
            updated_state.pop("error", None)
            return updated_state
        except Exception as exc:
            failed_state = dict(state)
            failed_state["roadmap"] = {}
            failed_state["error"] = f"RoadmapAgent failed: {exc}"
            return failed_state
