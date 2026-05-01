from wikirace.trap_detection import TrapConfig, is_local_basin


def test_basin_detected():
    cands = [{"target_proximity": 5}, {"target_proximity": 3}]
    assert is_local_basin(5, cands, TrapConfig())
