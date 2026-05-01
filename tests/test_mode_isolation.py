from scripts.run_phase2_ablations import MockAdapter, parse_yaml, MockTactical, MockStrategic
from wikirace.agent import run_game
from wikirace.strategies import build_strategy


def test_modes_use_same_loop_and_instances():
    cfg=parse_yaml('configs/stratified_navigator.yaml'); adapter=MockAdapter(); inst=adapter.get_game_instances('live','easy',1)[0]
    for mode in ['baseline','state_only','stratified','full']:
        strategy=build_strategy(mode,cfg,MockTactical(),MockStrategic(),adapter)
        res=run_game(inst,adapter,strategy,budget=30,logger=lambda e: None)
        assert 'status' in res
