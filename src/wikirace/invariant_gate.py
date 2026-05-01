from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class GateConfig:
    budget: int = 30
    hub_rejection_threshold: int = 3
    trap_target_score_threshold: int = 5
    score_decay_window: int = 3


class InvariantGate:
    def __init__(self, cfg: GateConfig):
        self.cfg = cfg

    def filter_candidates(
        self,
        candidates: List[Dict[str, Any]],
        visited: set,
        steps_used: int,
        allow_trap_relax: bool = False,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        stats = {"cycle_rejections": 0, "budget_rejections": 0, "trap_rejections": 0}
        valid = []
        for c in candidates:
            page = c["page"]
            if page in visited:
                stats["cycle_rejections"] += 1
                continue
            if steps_used + 1 + int(c.get("estimated_dist", self.cfg.budget)) > self.cfg.budget:
                stats["budget_rejections"] += 1
                continue
            trap_like = c.get("hub_score", 0) < self.cfg.hub_rejection_threshold and c.get("target_proximity", 0) < self.cfg.trap_target_score_threshold
            if trap_like and not allow_trap_relax:
                stats["trap_rejections"] += 1
                continue
            valid.append(c)
        return valid, stats

    @staticmethod
    def decay_trigger(score_history: List[float], window: int = 3) -> bool:
        if len(score_history) < window:
            return False
        recent = score_history[-window:]
        return all(recent[i] < recent[i - 1] for i in range(1, len(recent)))

    def choose_candidate(
        self,
        ranked_candidates: List[Dict[str, Any]],
        visited: set,
        steps_used: int,
    ) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        valid, stats = self.filter_candidates(ranked_candidates, visited, steps_used, allow_trap_relax=False)
        if valid:
            return valid[0], {**stats, "relaxed_trap": False}
        valid_relaxed, stats_relaxed = self.filter_candidates(ranked_candidates, visited, steps_used, allow_trap_relax=True)
        merged = {k: stats.get(k, 0) + stats_relaxed.get(k, 0) for k in set(stats) | set(stats_relaxed)}
        if valid_relaxed:
            return valid_relaxed[0], {**merged, "relaxed_trap": True}
        fallback = [c for c in ranked_candidates if c.get("page") not in visited]
        fallback.sort(key=lambda x: x.get("hub_score", 0), reverse=True)
        if fallback:
            return fallback[0], {**merged, "relaxed_trap": True, "fallback_hub": True}
        return None, {**merged, "relaxed_trap": True, "failure_risk": True}
