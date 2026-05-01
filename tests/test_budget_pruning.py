from wikirace.invariant_gate import InvariantGate, GateConfig


def test_budget_rejects():
    gate = InvariantGate(GateConfig(budget=3))
    choice, _ = gate.choose_candidate([
        {"page": "Y", "estimated_dist": 5, "hub_score": 9, "target_proximity": 9},
    ], set(), 0)
    assert choice is not None  # fallback still returns non-visited
