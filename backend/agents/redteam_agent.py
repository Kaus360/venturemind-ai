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


class RedTeamAgent(BaseAgent):
    """Agent responsible for adversarial critique of startup ideas."""

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            startup_idea = str(state.get("startup_idea", "")).strip()
            validation = state.get("validation", {})

            if not startup_idea:
                raise ValueError("Missing required 'startup_idea' in state.")
            if not validation:
                raise ValueError("Missing required 'validation' in state.")

            system_prompt = (
                "You are VentureMind AI's red-team critic agent. Aggressively attack the "
                "startup idea by identifying flaws, unrealistic assumptions, business "
                "viability issues, and scalability problems. Return a JSON object with "
                "these fields: critical_flaws, unrealistic_assumptions, viability_score, "
                "verdict. The verdict must be one of PASS, FAIL, or NEEDS_WORK. Return "
                "ONLY valid JSON. No explanation. No markdown."
            )
            user_prompt = (
                f"Startup idea: {startup_idea}\n\n"
                f"Validation context: {json.dumps(validation)}\n\n"
                "Critique this startup idea ruthlessly and assess whether it is actually "
                "viable. Return ONLY valid JSON."
            )

            response = await asyncio.to_thread(
                self.llm.invoke,
                self._build_messages(system_prompt, user_prompt),
            )

            content = response.content if hasattr(response, "content") else response
            content = clean_json(content)
            parsed_result = json.loads(content)

            updated_state = dict(state)
            updated_state["critic_feedback"] = parsed_result
            updated_state.pop("error", None)
            return updated_state
        except Exception as exc:
            failed_state = dict(state)
            failed_state["critic_feedback"] = {}
            failed_state["error"] = f"RedTeamAgent failed: {exc}"
            return failed_state
