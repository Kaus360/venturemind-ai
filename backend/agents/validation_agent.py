from __future__ import annotations

import asyncio
import json
import re
from typing import Any, Dict

from backend.agents.base_agent import BaseAgent
from backend.prompts.system_prompts import VALIDATION_PROMPT


def clean_json(text: str) -> str:
    text = text.strip()
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    return text.strip()


class ValidationAgent(BaseAgent):
    """Agent responsible for validating startup ideas."""

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            startup_idea = str(state.get("startup_idea", "")).strip()
            if not startup_idea:
                raise ValueError("Missing required 'startup_idea' in state.")

            system_prompt = VALIDATION_PROMPT
            user_prompt = f"Validate the feasibility of this startup idea: {startup_idea}"

            response = await asyncio.to_thread(
                self.llm.invoke,
                self._build_messages(system_prompt, user_prompt),
            )

            raw_content = response.content if hasattr(response, "content") else response
            raw_content = clean_json(raw_content)
            parsed_result = json.loads(raw_content)

            updated_state = dict(state)
            updated_state["validation"] = parsed_result
            updated_state.pop("error", None)
            return updated_state
        except Exception as exc:
            failed_state = dict(state)
            failed_state["validation"] = {}
            failed_state["error"] = f"ValidationAgent failed: {exc}"
            return failed_state
