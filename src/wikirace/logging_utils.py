import json
from pathlib import Path
from typing import Any, Dict


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def append_jsonl(path: str, record: Dict[str, Any]) -> None:
    p = Path(path)
    ensure_parent(p)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
