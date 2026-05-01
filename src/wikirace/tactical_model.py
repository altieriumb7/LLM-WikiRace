<<<<<<< codex/implement-stratified-navigator-for-llm-wikirace
import json, re
from typing import Any, Dict
from .api_client import FrontierAPIClient

SYSTEM_PROMPT=("You are not navigating directly. You are only scoring outgoing Wikipedia links. The deterministic controller will choose the move. Return JSON only.")

REQ={"page","target_proximity","hub_score","estimated_dist","milestone_progress","novelty","rationale"}

def _valid(c):
    return REQ.issubset(c.keys()) and 1<=int(c['target_proximity'])<=10 and 1<=int(c['hub_score'])<=10 and 1<=int(c['estimated_dist'])<=30 and 1<=int(c['milestone_progress'])<=10

class TacticalModel:
    def __init__(self,api:FrontierAPIClient,model:str,top_k:int=5,temperature:float=0): self.api=api; self.model=model; self.top_k=top_k; self.temperature=temperature
    def _parse(self,text):
        cleaned=re.sub(r"^```(?:json)?\s*|\s*```$","",text.strip(),flags=re.MULTILINE)
        data=json.loads(cleaned)
        if not isinstance(data,dict) or 'candidates' not in data or not isinstance(data['candidates'],list): raise ValueError('invalid schema')
        if any(not _valid(c) for c in data['candidates']): raise ValueError('invalid candidate')
        return data
    def rank(self,state:Dict[str,Any])->Dict[str,Any]:
        r=self.api.complete_json(self.model,SYSTEM_PROMPT,{"state":state,"top_k":self.top_k},temperature=self.temperature)
        try:return {"candidates":self._parse(r.text)['candidates'],"failure_reason":None}
        except Exception:
            rep=self.api.complete_json(self.model,SYSTEM_PROMPT,{"invalid_response":r.text,"repair":True},temperature=0)
            try:return {"candidates":self._parse(rep.text)['candidates'],"failure_reason":None}
            except Exception:return {"candidates":[],"failure_reason":"schema_repair_failed","event_type":"schema_repair_failed"}
=======
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
>>>>>>> main
