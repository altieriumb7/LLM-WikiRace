import pytest
from scripts.run_phase2_ablations import parse_yaml
from wikirace.modes import get_mode_config

cfg=parse_yaml('configs/stratified_navigator.yaml')

def test_load_modes():
    for m in ['baseline','state_only','stratified','full']:
        assert get_mode_config(m,cfg).name==m

def test_baseline_flags():
    m=get_mode_config('baseline',cfg)
    assert not m.use_json_state and not m.use_gate and not m.escape_logic and not m.use_beam_search

def test_state_only_flags():
    m=get_mode_config('state_only',cfg)
    assert m.use_json_state and m.enabled_invariants=={'acyclicity','budget'} and not m.use_backbone_planning

def test_stratified_flags():
    m=get_mode_config('stratified',cfg)
    assert m.periodic_replan and not m.decay_replan and not m.escape_logic

def test_full_flags():
    m=get_mode_config('full',cfg)
    assert {'acyclicity','budget','trap','score_decay'}.issubset(m.enabled_invariants)

def test_invalid_mode():
    with pytest.raises(ValueError): get_mode_config('bad',cfg)
