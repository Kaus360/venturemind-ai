from __future__ import annotations

import json
import re
from typing import Any, Dict

from backend.agents.base_agent import BaseAgent
from backend.prompts.system_prompts import PROBLEM_DISCOVERY_PROMPT


def clean_json(text: str) -> str:
    text = text.strip()
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    return text.strip()


class ProblemDiscoveryAgent(BaseAgent):
    """Agent responsible for discovering venture-scale startup problems."""

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            domain = str(state.get("domain", "")).strip()
            if not domain:
                raise ValueError("Missing required 'domain' in state.")

            system_prompt = PROBLEM_DISCOVERY_PROMPT
            user_prompt = (
                f"Domain: {state['domain']}\n\n"
                "Generate 3 startup problems for this domain. Return ONLY valid JSON."
            )

            response = self.llm.invoke(self._build_messages(system_prompt, user_prompt))
            content = response.content
            content = clean_json(content)
            parsed_result = json.loads(content)

            updated_state = dict(state)
            updated_state["problems"] = parsed_result
            updated_state.pop("error", None)
            return updated_state
        except Exception as exc:
            failed_state = dict(state)
            failed_state["problems"] = []
            failed_state["error"] = f"ProblemDiscoveryAgent failed: {exc}"
            return failed_state
