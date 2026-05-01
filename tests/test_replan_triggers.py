from wikirace.replan import evaluate_replan


def test_periodic_trigger():
    d=evaluate_replan(5,30,[],20,[])
    assert d.should_replan and d.reason=='periodic'

def test_decay_trigger():
    d=evaluate_replan(1,30,[9,7,5],20,[])
    assert d.should_replan and d.reason=='decay'

def test_no_decay_equal():
    d=evaluate_replan(1,30,[9,9,8],20,[])
    assert not d.should_replan

def test_trap_trigger():
    d=evaluate_replan(1,30,[9],5,[{'target_proximity':4}],5)
    assert d.should_escape and d.reason=='trap'
