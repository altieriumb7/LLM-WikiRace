from pathlib import Path
from wikirace.config import ModeConfig
from wikirace.strategies import build_strategy, BaselineStrategy, StatefulStrategy, StratifiedStrategy, FullStrategy

class A: pass

def test_factory_classes():
    a=A()
    assert isinstance(build_strategy(ModeConfig(strategy='baseline',model='x'),a),BaselineStrategy)
    assert isinstance(build_strategy(ModeConfig(strategy='state_only',model='x',deterministic_fallback=True),a),StatefulStrategy)
    assert isinstance(build_strategy(ModeConfig(strategy='stratified',tactical_model='x',strategic_model='y',deterministic_fallback=True),a),StratifiedStrategy)
    assert isinstance(build_strategy(ModeConfig(strategy='full',tactical_model='x',strategic_model='y',escape_threshold=10,deterministic_fallback=True),a),FullStrategy)

def test_runner_imports_factory_only():
    s=Path('scripts/run_phase2_ablations.py').read_text()
    assert 'build_strategy' in s
    assert 'BaselineStrategy(' not in s and 'StatefulStrategy(' not in s and 'StratifiedStrategy(' not in s and 'FullStrategy(' not in s
