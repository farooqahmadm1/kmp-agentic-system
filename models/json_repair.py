import json
import re
from typing import Any, Dict

class JSONRepair:
    """Cleans and extracts valid JSON objects from local 14B model outputs."""

    @classmethod
    def parse_or_repair(cls, raw_text: str) -> Dict[str, Any]:
        cleaned = raw_text.strip()

        # 1. Strip Markdown code fences: ```json ... ``` or ``` ... ```
        if "```" in cleaned:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
            if match:
                cleaned = match.group(1).strip()

        # 2. Extract outermost JSON object { ... } or array [ ... ]
        if not (cleaned.startswith("{") or cleaned.startswith("[")):
            match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", cleaned)
            if match:
                cleaned = match.group(1).strip()

        # 3. Fix trailing commas before closing braces/brackets (common local LLM syntax bug)
        cleaned = re.sub(r",\s*(\}|\])", r"\1", cleaned)

        # 4. Attempt standard json parse
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            # Fallback: Replace unescaped newlines within string values
            try:
                fixed_newlines = re.sub(r'(?<!\\)\n', r'\\n', cleaned)
                return json.loads(fixed_newlines)
            except Exception:
                raise ValueError(f"JSONRepair Failed to parse model output: {e}\nRaw output:\n{raw_text[:500]}")
