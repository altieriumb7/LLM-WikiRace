from typing import Any, Dict

from .state import initialize_state, transition_to


def run_game(*args, budget: int = 30, logger=lambda e: None) -> Dict[str, Any]:
    if len(args) == 4 and isinstance(args[0], str):
        start, target, strategy, adapter = args
        class _I:
            start_page = start
            target_page = target
        instance = _I()
    else:
        instance, adapter, strategy = args[:3]

    state = initialize_state(instance.start_page, instance.target_page, budget)
    counters = {"repeated_page_attempts": 0, "budget_rejections": 0, "schema_violations": 0, "trap_detections": 0, "strategic_replans": 0, "fallback_used": 0, "api_errors": 0}
    while state.steps_used < budget:
        if adapter.is_target(state.current_page, state.target_page):
            return {"status": "success", "state": state, **counters}
        try:
            links = adapter.get_outgoing_links(state.current_page)
        except Exception:
            counters["api_errors"] += 1
            return {"status": "failed", "failure_reason": "api_error", "state": state, **counters}

        move, meta = strategy.select_move(state, links)
        for k in counters:
            counters[k] += int(meta.get(k, 0))
        if move is None:
            return {"status": "failed", "failure_reason": meta.get("failure_reason", "invalid_model_move"), "state": state, **counters}
        if move in state.visited:
            counters["repeated_page_attempts"] += 1
        state = transition_to(state, move, float(meta.get("score", 0.0)))
        logger({"event_type": "step", "move": move, "meta": meta})
        if strategy.should_replan(state):
            strategy.on_replan(state, links)
    return {"status": "failed", "failure_reason": "budget_exhausted", "state": state, **counters}
