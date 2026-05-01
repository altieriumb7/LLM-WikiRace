from dataclasses import dataclass
from typing import Literal, List, Dict, Any


@dataclass
class ReplanDecision:
    should_replan: bool
    should_escape: bool
    reason: Literal["periodic", "decay", "trap", "none"]


def evaluate_replan(steps_used: int, budget: int, last_scores: List[float], out_degree: int, candidates: List[Dict[str, Any]], trap_threshold: int = 5) -> ReplanDecision:
    n = max(5, budget // 6)
    if steps_used > 0 and steps_used % n == 0:
        return ReplanDecision(True, False, "periodic")
    if len(last_scores) == 3 and last_scores[0] > last_scores[1] > last_scores[2]:
        return ReplanDecision(True, False, "decay")
    max_prox = max([c.get("target_proximity", 0) for c in candidates], default=0)
    if out_degree < 10 and max_prox <= trap_threshold:
        return ReplanDecision(False, True, "trap")
    return ReplanDecision(False, False, "none")
