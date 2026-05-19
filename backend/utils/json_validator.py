from __future__ import annotations

import json
import re


def clean_json(text: str) -> str:
    text = text.strip()
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    return text.strip()


def safe_parse(text: str) -> dict:
    try:
        return json.loads(clean_json(text))
    except Exception:
        return {}


def validate_scores(data: dict, required_keys: list) -> bool:
    for key in required_keys:
        if key not in data:
            return False
        value = data[key]
        if not isinstance(value, (int, float)):
            return False
        if float(value) == 0:
            return False
    return True
