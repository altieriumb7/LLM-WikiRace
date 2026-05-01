from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class TrapConfig:
    outdegree_threshold: int = 10
    target_score_threshold: int = 5


def is_local_basin(out_degree: int, candidates: List[Dict[str, Any]], cfg: TrapConfig) -> bool:
    if not candidates:
        return out_degree < cfg.outdegree_threshold
    max_prox = max(c.get("target_proximity", 0) for c in candidates)
    return out_degree < cfg.outdegree_threshold and max_prox <= cfg.target_score_threshold
