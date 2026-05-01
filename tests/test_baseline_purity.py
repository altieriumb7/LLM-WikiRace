import ast, inspect
from wikirace.strategies import BaselineStrategy

def test_baseline_no_forbidden_symbols():
    source=inspect.getsource(BaselineStrategy); tree=ast.parse(source)
    forbidden={'tactical','gate','invariant_gate','escape','replan','strategic','fallback','TacticalCandidate','TacticalResponse','StrategicResponse'}
    names={n.id for n in ast.walk(tree) if isinstance(n,ast.Name)}
    attrs={n.attr for n in ast.walk(tree) if isinstance(n,ast.Attribute)}
    assert not (forbidden & (names|attrs))
