from pathlib import Path
from wikirace.config import load_mode


def test_load_modes():
    for m in ['baseline','state_only','stratified','full']:
        assert load_mode(Path(f'configs/modes/{m}.yaml')).strategy==m


def test_baseline_flags():
    m=load_mode(Path('configs/modes/baseline.yaml'))
    assert (m.strategy=='baseline') and (m.model is not None) and (m.strategic_model is None)


def test_state_only_flags():
    m=load_mode(Path('configs/modes/state_only.yaml'))
    assert m.strategy=='state_only' and m.model is not None


def test_stratified_flags():
    m=load_mode(Path('configs/modes/stratified.yaml'))
    assert m.strategy=='stratified' and m.tactical_model and m.strategic_model


def test_full_flags():
    m=load_mode(Path('configs/modes/full.yaml'))
    assert m.strategy=='full' and m.escape_threshold is not None
