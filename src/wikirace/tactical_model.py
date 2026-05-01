import json
import re
from typing import Any, Dict, List

from .api_client import FrontierAPIClient

SYSTEM_PROMPT = (
    "You are not navigating directly. You are only scoring outgoing Wikipedia links. "
    "The deterministic controller will choose the move. Return JSON only."
)


class TacticalModel:
    def __init__(self, api: FrontierAPIClient, model: str, top_k: int = 5, temperature: float = 0):
        self.api = api
        self.model = model
        self.top_k = top_k
        self.temperature = temperature

    def _parse(self, text: str) -> Dict[str, Any]:
        cleaned = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
        return json.loads(cleaned)

    def rank(self, state: Dict[str, Any]) -> Dict[str, Any]:
        if state.get("mock_ranker"):
            return state["mock_ranker"](state)
        payload = {"instruction": "Return {candidates:[...]} with required fields", "state": state, "top_k": self.top_k}
        result = self.api.complete_json(self.model, SYSTEM_PROMPT, payload, temperature=self.temperature)
        try:
            data = self._parse(result.text)
        except Exception:
            repair_payload = {"invalid_response": result.text, "instruction": "Repair to valid JSON only with schema {candidates:[...]}"}
            repaired = self.api.complete_json(self.model, SYSTEM_PROMPT, repair_payload, temperature=0)
            data = self._parse(repaired.text)
        return data
