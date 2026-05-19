from __future__ import annotations

import asyncio
import json
import re
from typing import Any, Dict

from backend.agents.base_agent import BaseAgent
from backend.prompts.system_prompts import SOLUTION_GENERATOR_PROMPT


def clean_json(text: str) -> str:
    text = text.strip()
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    return text.strip()


class SolutionGeneratorAgent(BaseAgent):
    """Agent responsible for generating startup solutions from a problem statement."""

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            problem_statement = str(state.get("problem_statement", "")).strip()
            if not problem_statement:
                raise ValueError("Missing required 'problem_statement' in state.")

            system_prompt = SOLUTION_GENERATOR_PROMPT
            user_prompt = (
                "Generate a startup solution for the following problem statement: "
                f"{problem_statement}"
            )

            response = await asyncio.to_thread(
                self.llm.invoke,
                self._build_messages(system_prompt, user_prompt),
            )

            raw_content = response.content if hasattr(response, "content") else response
            raw_content = clean_json(raw_content)
            parsed_result = json.loads(raw_content)

            updated_state = dict(state)
            updated_state["solution"] = parsed_result
            updated_state.pop("error", None)
            return updated_state
        except Exception as exc:
            failed_state = dict(state)
            failed_state["solution"] = {}
            failed_state["error"] = f"SolutionGeneratorAgent failed: {exc}"
            return failed_state
