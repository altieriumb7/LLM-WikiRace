from dataclasses import dataclass, field
from typing import Any, Dict, List, Set


@dataclass
class BeamState:
    current_page: str
    path: List[str]
    visited: Set[str]
    steps_used: int
    score_history: List[float] = field(default_factory=list)
    strategic_backbone: List[str] = field(default_factory=list)
    current_milestone: str = ""
    status: str = "active"


def rank_beams(beams: List[BeamState]) -> List[BeamState]:
    return sorted(
        beams,
        key=lambda b: (
            0 if b.status == "success" else 1,
            b.steps_used,
            -(b.score_history[-1] if b.score_history else 0),
        ),
    )
