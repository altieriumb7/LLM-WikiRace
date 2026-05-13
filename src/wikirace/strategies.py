import ast
from dataclasses import dataclass, field
from typing import Protocol

from .api_client import FrontierAPIClient
from .config import ModeConfig
from .fallback import select_fallback
from .replan import evaluate_replan
from .oracle import DistanceOracle
from .strategic_model import StrategicModel
from .tactical_model import TacticalModel


class NavigationStrategy(Protocol):
    def select_move(self, state, candidates): ...
    def should_replan(self, state): ...
    def on_replan(self, state, candidates): ...


@dataclass
class BaselineStrategy:
    model: any
    messages: list[dict[str, str]] = field(default_factory=list)

    def select_move(self, state, candidates):
        prompt = (
            f"Current page: {state.current_page}\n"
            f"Target page: {state.target_page}\n"
            f"Outgoing links: {candidates}\n"
            "Choose exactly one next link from outgoing links."
        )
        self.messages.append({"role": "user", "content": prompt})
        out = self.model.chat(self.messages)
        move = str(out).strip()
        self.messages.append({"role": "assistant", "content": move})
        if move not in candidates:
            return None, {"failure_reason": "invalid_model_move"}
        return move, {}

    def should_replan(self, state):
        return False

    def on_replan(self, state, candidates):
        return None


@dataclass
class StatefulStrategy:
    model: any
    adapter: any
    top_k: int
    deterministic_fallback: bool

    def select_move(self, state, candidates):
        ranked = self.model.rank({"current_page": state.current_page, "target_page": state.target_page, "visited": list(state.visited), "outgoing_links": candidates})
        for c in ranked.get("candidates", [])[: self.top_k]:
            if c["page"] in state.visited:
                continue
            if state.steps_used + 1 + int(c.get("estimated_dist", 30)) > state.budget:
                continue
            return c["page"], {}
        if self.deterministic_fallback:
            fb = select_fallback(state.current_page, candidates, set(state.visited), {})
            if fb.terminal:
                return None, {"failure_reason": "loop_exhausted"}
            return fb.selected_page, {"fallback_used": 1}
        return None, {"failure_reason": "no_move"}

    def should_replan(self, state):
        return False

    def on_replan(self, state, candidates):
        return None


@dataclass
class StratifiedStrategy(StatefulStrategy):
    strategic_model: any = None
    replan_interval: int = 5
    decay_replan: bool = False

    def should_replan(self, state):
        return state.steps_used > 0 and state.steps_used % self.replan_interval == 0

    def on_replan(self, state, candidates):
        if self.strategic_model:
            self.strategic_model.plan({"current": state.current_page, "target": state.target_page})
        return None


@dataclass
class FullStrategy(StratifiedStrategy):
    escape_threshold: int = 10
    oracle: DistanceOracle | None = None

    def select_move(self, state, candidates):
        if self.oracle is not None and candidates:
            distances = self.oracle.batch_distance(list(candidates), state.target_page)
            known = sorted([(c, d) for c, d in distances.items() if d is not None], key=lambda x: x[1])
            for candidate, _dist in known:
                if candidate in state.visited:
                    continue
                if state.steps_used + 1 > state.budget:
                    continue
                return candidate, {}
        return super().select_move(state, candidates)

    def should_replan(self, state):
        d = evaluate_replan(state.steps_used, state.budget, [3, 2, 1], 5, [{"target_proximity": 1}], 5)
        return super().should_replan(state) or (self.decay_replan and d.reason == "decay")


class _BaselineModel:
    def chat(self, messages):
        text = messages[-1]["content"]
        links = text.split("Outgoing links: ")[1].split("\n")[0]
        arr = ast.literal_eval(links) if links.startswith("[") else []
        return arr[0] if arr else ""


class _OpenAIBaselineModel:
    def __init__(self, api: FrontierAPIClient, model: str):
        self.api = api
        self.model = model

    def chat(self, messages):
        result = self.api.complete_json(
            self.model,
            "Choose exactly one page title from the provided outgoing links. Return only the page title.",
            {"messages": messages},
            temperature=0,
        )
        return str(result.text).strip().strip('"')


class _Ranker:
    def rank(self, payload):
        return {"candidates": [{"page": x, "estimated_dist": 1} for x in payload.get("outgoing_links", [])]}


class _Planner:
    def plan(self, payload):
        return {"backbone": ["X"]}


def build_strategy(config: ModeConfig, adapter, use_real_models: bool = False) -> NavigationStrategy:
    api = FrontierAPIClient() if use_real_models else None
    if use_real_models and not api.available():
        raise RuntimeError("OPENAI_API_KEY is required when --real-models is set")
    if config.strategy == "baseline":
        model = _OpenAIBaselineModel(api, config.model) if api else _BaselineModel()
        return BaselineStrategy(model=model)
    if config.strategy == "state_only":
        model = TacticalModel(api, config.model, top_k=config.top_k) if api else _Ranker()
        return StatefulStrategy(model=model, adapter=adapter, top_k=config.top_k, deterministic_fallback=config.deterministic_fallback)
    if config.strategy == "stratified":
        model = TacticalModel(api, config.tactical_model, top_k=config.top_k) if api else _Ranker()
        planner = StrategicModel(api, config.strategic_model) if api else _Planner()
        return StratifiedStrategy(model=model, adapter=adapter, top_k=config.top_k, deterministic_fallback=config.deterministic_fallback, strategic_model=planner, replan_interval=config.replan_interval, decay_replan=config.decay_replan)
    if config.strategy == "full":
        oracle = DistanceOracle(config.oracle_db_path) if config.oracle_db_path else None
        model = TacticalModel(api, config.tactical_model, top_k=config.top_k) if api else _Ranker()
        planner = StrategicModel(api, config.strategic_model) if api else _Planner()
        return FullStrategy(model=model, adapter=adapter, top_k=config.top_k, deterministic_fallback=config.deterministic_fallback, strategic_model=planner, replan_interval=config.replan_interval, decay_replan=config.decay_replan, escape_threshold=config.escape_threshold or 10, oracle=oracle)
    raise ValueError(config.strategy)
