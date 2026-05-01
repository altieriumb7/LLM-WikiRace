from pathlib import Path

from wikirace.config import load_mode
from wikirace.strategies import BaselineStrategy, StatefulStrategy, StratifiedStrategy, FullStrategy, build_strategy


class Adapter: ...


def test_mode_behaviors():
    adapter=Adapter()
    baseline=build_strategy(load_mode(Path('configs/modes/baseline.yaml')), adapter)
    state_only=build_strategy(load_mode(Path('configs/modes/state_only.yaml')), adapter)
    stratified=build_strategy(load_mode(Path('configs/modes/stratified.yaml')), adapter)
    full=build_strategy(load_mode(Path('configs/modes/full.yaml')), adapter)

    assert isinstance(baseline, BaselineStrategy)
    assert isinstance(state_only, StatefulStrategy) and not isinstance(state_only, StratifiedStrategy)
    assert isinstance(stratified, StratifiedStrategy) and not isinstance(stratified, FullStrategy)
    assert isinstance(full, FullStrategy)
