from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Protocol, Tuple
from .fallback import select_fallback
from .modes import ModeConfig, get_mode_config
from .replan import evaluate_replan


class NavigationStrategy(Protocol):
    def select_move(self, state, candidates: List[str]) -> Tuple[str | None, Dict]: ...
    def should_replan(self, state) -> bool: ...
    def on_replan(self, state, candidates: List[str]) -> None: ...


@dataclass
class BaselineStrategy:
    tactical: any
    chat_history: List[Dict]
    def select_move(self, state, candidates):
        ranked = self.tactical.rank({"current_page": state.current_page, "target_page": state.target_page, "steps_used": state.steps_used, "outgoing_links": candidates, "chat_history": self.chat_history})
        if not ranked.get("candidates"): return None, {"failure_reason": "invalid_model_move", "schema_violations": 1}
        move = ranked["candidates"][0]["page"]
        if move not in candidates: return None, {"failure_reason": "invalid_model_move"}
        self.chat_history.append({"from": state.current_page, "to": move})
        return move, {"score": ranked['candidates'][0].get('target_proximity', 0)}
    def should_replan(self, state): return False
    def on_replan(self, state, candidates): return None


@dataclass
class StructuredStrategy:
    mode: ModeConfig
    tactical: any
    strategic: any
    adapter: any

    def select_move(self, state, candidates):
        ranked_resp = self.tactical.rank({"current_page": state.current_page, "target_page": state.target_page, "steps_used": state.steps_used, "budget": state.budget, "visited": list(state.visited), "outgoing_links": candidates, "last_scores": list(state.last_scores), "strategic_backbone": list(state.backbone_plan or ()), "current_milestone": state.current_milestone})
        ranked = ranked_resp.get("candidates", [])
        meta = {"schema_violations": 1 if ranked_resp.get("failure_reason") else 0}
        legal = []
        for c in ranked[: self.mode.top_k]:
            if "acyclicity" in self.mode.enabled_invariants and c["page"] in state.visited:
                meta["repeated_page_attempts"] = meta.get("repeated_page_attempts", 0) + 1
                continue
            if "budget" in self.mode.enabled_invariants and state.steps_used + 1 + int(c.get("estimated_dist", 30)) > state.budget:
                meta["budget_rejections"] = meta.get("budget_rejections", 0) + 1
                continue
            legal.append(c)
        if legal:
            return legal[0]["page"], {**meta, "score": legal[0].get("target_proximity", 0)}
        if self.mode.deterministic_fallback:
            metrics = self.adapter.get_link_metrics(candidates)
            fb = select_fallback(state.current_page, candidates, set(state.visited), {k: v.__dict__ for k, v in metrics.items()})
            if fb.terminal:
                return None, {**meta, "failure_reason": "loop_exhausted"}
            return fb.selected_page, {**meta, "fallback_used": 1, "score": 0}
        return None, {**meta, "failure_reason": "invalid_model_move"}

    def should_replan(self, state):
        if not self.mode.use_backbone_planning: return False
        d = evaluate_replan(state.steps_used, state.budget, list(state.last_scores), 20, [], 5)
        if d.reason == "periodic" and self.mode.periodic_replan: return True
        if d.reason == "decay" and self.mode.decay_replan: return True
        return False

    def on_replan(self, state, candidates):
        if self.mode.strategic_model:
            self.strategic.plan({"current_page": state.current_page, "target_page": state.target_page, "steps_used": state.steps_used, "budget": state.budget, "visited": list(state.visited), "outgoing_links": candidates})


def build_strategy(mode_name: str, cfg: dict, tactical, strategic, adapter) -> NavigationStrategy:
    mode = get_mode_config(mode_name, cfg)
    if mode.baseline_chat_history:
        return BaselineStrategy(tactical=tactical, chat_history=[])
    return StructuredStrategy(mode=mode, tactical=tactical, strategic=strategic, adapter=adapter)


def build_strategy_with_models(mode_name: str, cfg: dict, api_client, adapter, mock: bool=False):
    from .tactical_model import TacticalModel
    from .strategic_model import StrategicModel
    if mock:
        class _MT:
            def rank(self,state):
                links=state.get("outgoing_links",[])
                return {"candidates":[{"page":p,"target_proximity":max(1,10-i),"hub_score":5,"estimated_dist":1,"milestone_progress":5,"novelty":True,"rationale":"mock"} for i,p in enumerate(links)]}
        class _MS:
            def plan(self,state): return {"backbone":["X"],"current_milestone":"X"}
        tactical,strategic=_MT(),_MS()
    else:
        m=get_mode_config(mode_name,cfg)
        tactical=TacticalModel(api_client,m.tactical_model,top_k=m.top_k)
        strategic=StrategicModel(api_client,m.strategic_model or m.tactical_model)
    return build_strategy(mode_name,cfg,tactical,strategic,adapter)
