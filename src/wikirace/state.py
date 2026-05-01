from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Literal, Optional, Tuple, FrozenSet


@dataclass(frozen=True)
class NavigatorState:
    current_page: str
    target_page: str
    steps_used: int
    budget: int = 30
    visited: FrozenSet[str] = field(default_factory=frozenset)
    path: Tuple[str, ...] = field(default_factory=tuple)
    phase: Literal["progress", "replan", "escape"] = "progress"
    backbone_plan: Optional[Tuple[str, ...]] = None
    current_milestone: Optional[str] = None
    last_scores: Tuple[float, ...] = field(default_factory=tuple)
    last_replan_step: Optional[int] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.steps_used < 0 or self.steps_used > self.budget: raise ValueError("steps_used must be between 0 and budget")
        if self.current_page not in self.visited: raise ValueError("current_page must be inside visited")
        if len(self.path) != self.steps_used + 1: raise ValueError("len(path) must equal steps_used + 1")
        if len(self.last_scores) > 3: raise ValueError("last_scores must keep only last 3 accepted tactical scores")

def initialize_state(start_page: str, target_page: str, budget: int = 30) -> NavigatorState:
    return NavigatorState(start_page, target_page, 0, budget, frozenset({start_page}), (start_page,))

def transition_to(state: NavigatorState, next_page: str, score: float, phase=None, backbone_plan=None, current_milestone=None) -> NavigatorState:
    return NavigatorState(next_page, state.target_page, state.steps_used + 1, state.budget, frozenset(set(state.visited)|{next_page}), tuple(list(state.path)+[next_page]), phase or state.phase, tuple(backbone_plan) if backbone_plan is not None else state.backbone_plan, current_milestone if current_milestone is not None else state.current_milestone, tuple((list(state.last_scores)+[float(score)])[-3:]), state.last_replan_step, dict(state.metadata))

def with_phase(state: NavigatorState, phase: Literal["progress", "replan", "escape"]) -> NavigatorState:
    return NavigatorState(**{**state.__dict__,"phase":phase})

def with_backbone(state: NavigatorState, backbone_plan, current_milestone) -> NavigatorState:
    return NavigatorState(**{**state.__dict__,"backbone_plan":tuple(backbone_plan),"current_milestone":current_milestone})
