import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .api_client import FrontierAPIClient
from .navigator import NavigatorConfig, StratifiedNavigator
from .strategic_model import StrategicModel
from .tactical_model import TacticalModel


class MockGraphAdapter:
    def __init__(self, graph: Dict[str, List[str]]):
        self.graph = graph

    def get_outgoing_links(self, page: str) -> List[str]:
        return self.graph.get(page, [])


def load_config(path: str) -> NavigatorConfig:
    data: Dict[str, Any] = {}
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        k, v = line.split(":", 1)
        key = k.strip()
        val = v.strip().strip('"').strip("'")
        if val.isdigit():
            data[key] = int(val)
        else:
            try:
                data[key] = float(val)
            except ValueError:
                data[key] = val
    return NavigatorConfig(**{k: data[k] for k in NavigatorConfig.__annotations__.keys() if k in data})


def mock_ranker(state: Dict[str, Any]) -> Dict[str, Any]:
    candidates = []
    for i, p in enumerate(state["outgoing_links"]):
        prox = max(1, 10 - i)
        hub = 8 if "Hub" in p or p in ["Science", "Biology", "Computer_science"] else 4
        est = max(1, 12 - prox)
        milestone = 9 if p in state.get("strategic_backbone", []) else 5
        novelty = p not in state.get("visited", [])
        bonus = 1 if novelty else 0
        score = 0.4 * prox + 0.25 * milestone + 0.2 * hub + 0.15 * bonus
        candidates.append({"page": p, "target_proximity": prox, "hub_score": hub, "estimated_dist": est, "milestone_progress": milestone, "novelty": novelty, "rationale": "mock", "combined_score": score})
    candidates.sort(key=lambda x: x["combined_score"], reverse=True)
    return {"candidates": candidates[: max(5, len(candidates))]}


def mock_planner(state: Dict[str, Any]) -> Dict[str, Any]:
    return {"backbone": ["Science", "Biology", state["target_page"]], "current_milestone": "Science", "reasoning_summary": "mock plan", "escape_advice": "prefer hubs"}


def run_instances(instances: Iterable[Dict[str, str]], cfg: NavigatorConfig, mode: str) -> List[Dict[str, Any]]:
    graph = {
        "Backpropagation": ["Gradient_descent", "Artificial_neural_network", "Computer_science"],
        "Computer_science": ["Science", "Mathematics"],
        "Science": ["Biology", "Physics", "Chemistry"],
        "Biology": ["Photosynthesis", "Cell_(biology)"],
    }
    api = FrontierAPIClient()
    tactical = TacticalModel(api, "gpt-4o-mini", top_k=cfg.top_k)
    strategic = StrategicModel(api, "gpt-4o")
    nav = StratifiedNavigator(MockGraphAdapter(graph), tactical, strategic, cfg)
    rows = []
    for inst in instances:
        nav.tactical.rank = lambda s: mock_ranker({**s, "mock_ranker": mock_ranker})
        nav.strategic.plan = lambda s: mock_planner({**s, "mock_planner": mock_planner})
        out = nav.run(inst["start_page"], inst["target_page"], mode=mode)
        rows.append({**inst, **out, "mode": mode})
    return rows
