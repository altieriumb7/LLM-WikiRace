import json
import re
from typing import Any, Dict

from .api_client import FrontierAPIClient

SYSTEM_PROMPT = (
    "You are not choosing the next link. You are producing a high-level backbone of Wikipedia-style hubs "
    "that can guide local navigation. Return JSON only."
)


class StrategicModel:
    def __init__(self, api: FrontierAPIClient, model: str, temperature: float = 0):
        self.api = api
        self.model = model
        self.temperature = temperature

    def _parse(self, text: str) -> Dict[str, Any]:
        cleaned = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
        return json.loads(cleaned)

    def plan(self, state: Dict[str, Any]) -> Dict[str, Any]:
        if state.get("mock_planner"):
            return state["mock_planner"](state)
        payload = {"instruction": "Return {backbone,current_milestone,reasoning_summary,escape_advice}", "state": state}
        result = self.api.complete_json(self.model, SYSTEM_PROMPT, payload, temperature=self.temperature)
        try:
            return self._parse(result.text)
        except Exception:
            repair = self.api.complete_json(self.model, SYSTEM_PROMPT, {"invalid_response": result.text, "repair": True}, temperature=0)
            return self._parse(repair.text)
