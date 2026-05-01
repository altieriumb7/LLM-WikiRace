import json,re
from typing import Any, Dict
from .api_client import FrontierAPIClient

SYSTEM_PROMPT=("You are not choosing the next link. You are producing a high-level backbone of Wikipedia-style hubs that can guide local navigation. Return JSON only.")

class StrategicModel:
    def __init__(self,api:FrontierAPIClient,model:str,temperature:float=0): self.api=api; self.model=model; self.temperature=temperature
    def _parse(self,text):
        cleaned=re.sub(r"^```(?:json)?\s*|\s*```$","",text.strip(),flags=re.MULTILINE)
        d=json.loads(cleaned)
        for k in ['backbone','current_milestone','reasoning_summary']:
            if k not in d: raise ValueError('invalid schema')
        return d
    def plan(self,state:Dict[str,Any])->Dict[str,Any]:
        r=self.api.complete_json(self.model,SYSTEM_PROMPT,{"state":state},temperature=self.temperature)
        try:return self._parse(r.text)
        except Exception:
            rep=self.api.complete_json(self.model,SYSTEM_PROMPT,{"invalid_response":r.text,"repair":True},temperature=0)
            try:return self._parse(rep.text)
            except Exception:return {"backbone":[],"current_milestone":"","reasoning_summary":"repair failed","escape_advice":None,"event_type":"schema_repair_failed"}
