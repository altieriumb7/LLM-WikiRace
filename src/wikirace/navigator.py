from dataclasses import dataclass
from typing import Any, Dict, List

from .beam_search import BeamState, rank_beams
from .invariant_gate import GateConfig, InvariantGate
from .trap_detection import TrapConfig, is_local_basin


@dataclass
class NavigatorConfig:
    budget: int = 30
    beam_width: int = 5
    top_k: int = 5
    periodic_replan_steps: int = 6
    score_decay_window: int = 3
    trap_outdegree_threshold: int = 10
    trap_target_score_threshold: int = 5


class StratifiedNavigator:
    def __init__(self, graph_adapter, tactical_model, strategic_model, cfg: NavigatorConfig):
        self.graph = graph_adapter
        self.tactical = tactical_model
        self.strategic = strategic_model
        self.cfg = cfg
        self.gate = InvariantGate(GateConfig(budget=cfg.budget, score_decay_window=cfg.score_decay_window, trap_target_score_threshold=cfg.trap_target_score_threshold))

    def run(self, start_page: str, target_page: str, mode: str = "full_stratified") -> Dict[str, Any]:
        beams = [BeamState(current_page=start_page, path=[start_page], visited={start_page}, steps_used=0)]
        metrics = {"trap_detections": 0, "strategic_replans": 0, "budget_rejections": 0, "repeated_page_attempts": 0, "api_calls": 0}
        while beams:
            new_beams = []
            for beam in beams:
                if beam.current_page == target_page:
                    beam.status = "success"
                    return {"success": True, "path": beam.path, "steps": beam.steps_used, "metrics": metrics}
                if beam.steps_used >= self.cfg.budget:
                    continue
                links = self.graph.get_outgoing_links(beam.current_page)
                state = {
                    "current_page": beam.current_page,
                    "target_page": target_page,
                    "steps_used": beam.steps_used,
                    "budget": self.cfg.budget,
                    "visited": list(beam.visited),
                    "phase": "progress",
                    "outgoing_links": links,
                    "strategic_backbone": beam.strategic_backbone,
                    "current_milestone": beam.current_milestone,
                }
                ranked = self.tactical.rank(state).get("candidates", [])
                basin = is_local_basin(len(links), ranked, TrapConfig(self.cfg.trap_outdegree_threshold, self.cfg.trap_target_score_threshold))
                if basin:
                    metrics["trap_detections"] += 1
                choice, stats = self.gate.choose_candidate(ranked, beam.visited, beam.steps_used)
                metrics["budget_rejections"] += stats.get("budget_rejections", 0)
                metrics["repeated_page_attempts"] += stats.get("cycle_rejections", 0)
                if not choice or mode == "baseline_chat":
                    continue
                candidates = [choice] if self.cfg.beam_width == 1 else ranked[: self.cfg.beam_width]
                for c in candidates:
                    if c["page"] in beam.visited:
                        continue
                    nb = BeamState(
                        current_page=c["page"],
                        path=beam.path + [c["page"]],
                        visited=set(beam.visited) | {c["page"]},
                        steps_used=beam.steps_used + 1,
                        score_history=beam.score_history + [c.get("combined_score", c.get("target_proximity", 0))],
                        strategic_backbone=beam.strategic_backbone,
                        current_milestone=beam.current_milestone,
                    )
                    if self.gate.decay_trigger(nb.score_history, self.cfg.score_decay_window) or nb.steps_used % self.cfg.periodic_replan_steps == 0:
                        if mode in ("tactical_strategic", "full_stratified"):
                            plan = self.strategic.plan({"current_page": nb.current_page, "target_page": target_page, "visited": list(nb.visited), "steps_used": nb.steps_used, "budget": self.cfg.budget, "outgoing_links": self.graph.get_outgoing_links(nb.current_page), "recent_trail": nb.path[-5:], "failed_candidates": [], "previous_backbone": nb.strategic_backbone})
                            nb.strategic_backbone = plan.get("backbone", nb.strategic_backbone)
                            nb.current_milestone = plan.get("current_milestone", nb.current_milestone)
                            metrics["strategic_replans"] += 1
                    new_beams.append(nb)
            beams = rank_beams(new_beams)[: self.cfg.beam_width]
        return {"success": False, "path": [], "steps": self.cfg.budget, "metrics": metrics, "failure_reason": "no_legal_beams"}
