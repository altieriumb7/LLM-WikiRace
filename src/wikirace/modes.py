from dataclasses import dataclass
from typing import Literal, Optional, Set

Invariant = Literal["acyclicity", "budget", "trap", "score_decay"]
ModeName = Literal["baseline", "state_only", "stratified", "full"]


@dataclass(frozen=True)
class ModeConfig:
    name: ModeName
    tactical_model: str
    strategic_model: Optional[str]
    use_json_state: bool
    use_gate: bool
    enabled_invariants: Set[Invariant]
    use_backbone_planning: bool
    periodic_replan: bool
    decay_replan: bool
    trap_detection: bool
    escape_logic: bool
    use_beam_search: bool
    beam_width: int
    top_k: int
    baseline_chat_history: bool
    deterministic_fallback: bool


def get_mode_config(mode_name: str, base_config: dict) -> ModeConfig:
    modes = base_config.get("modes", {})
    if mode_name not in modes:
        raise ValueError(f"Unknown mode '{mode_name}'")
    m = modes[mode_name]
    return ModeConfig(
        name=mode_name,
        tactical_model=m["tactical_model"],
        strategic_model=m.get("strategic_model"),
        use_json_state=bool(m["use_json_state"]),
        use_gate=bool(m["use_gate"]),
        enabled_invariants=set(m.get("enabled_invariants", [])),
        use_backbone_planning=bool(m["use_backbone_planning"]),
        periodic_replan=bool(m["periodic_replan"]),
        decay_replan=bool(m["decay_replan"]),
        trap_detection=bool(m["trap_detection"]),
        escape_logic=bool(m["escape_logic"]),
        use_beam_search=bool(m["use_beam_search"]),
        beam_width=int(m["beam_width"]),
        top_k=int(m.get("top_k", base_config.get("top_k", 5))),
        baseline_chat_history=bool(m["baseline_chat_history"]),
        deterministic_fallback=bool(m["deterministic_fallback"]),
    )
