import ast
import inspect

from wikirace.strategies import BaselineStrategy

FORBIDDEN_BASELINE_SYMBOLS = {
    'GameState','visited','visited_pages','path','tactical','TacticalCandidate','TacticalResponse','strategic',
    'StrategicResponse','fallback','replan','escape','gate','invariant_gate','BaseModel','model_json_schema','json_schema'
}


def test_baseline_no_forbidden_symbols():
    source = inspect.getsource(BaselineStrategy)
    tree = ast.parse(source)
    seen = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            seen.add(node.id)
        elif isinstance(node, ast.Attribute):
            seen.add(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            seen.add(node.value)

    assert not (FORBIDDEN_BASELINE_SYMBOLS & seen)


def test_baseline_uses_raw_chat_not_structured_rankers():
    source = inspect.getsource(BaselineStrategy)
    tree = ast.parse(source)
    called = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                called.add(node.func.attr)
            elif isinstance(node.func, ast.Name):
                called.add(node.func.id)

    assert 'chat' in called
    assert 'rank' not in called
    assert 'plan' not in called
    assert 'select_fallback' not in called
