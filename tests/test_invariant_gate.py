from wikirace.invariant_gate import GateConfig, InvariantGate


def test_cycle_and_budget_pruning():
    gate = InvariantGate(GateConfig(budget=5))
    cands = [
        {"page": "A", "estimated_dist": 3, "hub_score": 6, "target_proximity": 6},
        {"page": "B", "estimated_dist": 9, "hub_score": 6, "target_proximity": 6},
    ]
    valid, stats = gate.filter_candidates(cands, {"A"}, 1)
    assert len(valid) == 0
    assert stats["cycle_rejections"] == 1
    assert stats["budget_rejections"] == 1
