from wikirace.invariant_gate import GateConfig, InvariantGate


def test_choose_candidate_skips_visited():
    gate = InvariantGate(GateConfig())
    choice, _ = gate.choose_candidate([
        {"page": "X", "estimated_dist": 2, "hub_score": 9, "target_proximity": 9},
        {"page": "Y", "estimated_dist": 2, "hub_score": 9, "target_proximity": 9},
    ], {"X"}, 0)
    assert choice["page"] == "Y"
