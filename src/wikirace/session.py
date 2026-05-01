import json
from pathlib import Path
from typing import Any, Dict
from .state import NavigatorState

def save_checkpoint(path: str, payload: Dict[str, Any]) -> None:
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(payload, indent=2))

def load_checkpoint(path: str) -> Dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    payload["state"] = NavigatorState(**payload["state"])
    return payload
