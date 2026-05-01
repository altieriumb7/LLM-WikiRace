import pytest
from wikirace.state import NavigatorState, initialize_state, transition_to

def test_valid_initial_state_passes(): assert initialize_state('A','B',30).steps_used==0
def test_invalid_steps_used_gt_budget_fails():
    with pytest.raises(ValueError): NavigatorState('A','B',31,30,frozenset({'A'}),('A',))
def test_current_page_not_in_visited_fails():
    with pytest.raises(ValueError): NavigatorState('A','B',0,30,frozenset({'X'}),('A',))
def test_path_len_inconsistent_fails():
    with pytest.raises(ValueError): NavigatorState('A','B',1,30,frozenset({'A'}),('A',))
def test_transition_appends_one_and_scores_capped():
    s=initialize_state('A','B'); s=transition_to(s,'C',1.0); assert s.path==('A','C')
    s=transition_to(s,'D',2.0); s=transition_to(s,'E',3.0); s=transition_to(s,'F',4.0); assert s.last_scores==(2.0,3.0,4.0)
