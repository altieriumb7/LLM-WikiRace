import sqlite3

from wikirace.oracle import DistanceOracle
from wikirace.strategies import FullStrategy
from wikirace.state import initialize_state


def _mk_db(path):
    conn=sqlite3.connect(path)
    conn.execute("CREATE TABLE distances (target TEXT NOT NULL, source TEXT NOT NULL, dist INTEGER NOT NULL, PRIMARY KEY(target, source));")
    conn.execute("INSERT INTO distances(target,source,dist) VALUES ('Target','SemanticallyCloseButFar',12)")
    conn.execute("INSERT INTO distances(target,source,dist) VALUES ('Target','SemanticallyOddButNear',3)")
    conn.commit(); conn.close()


def test_distance_oracle_lookup(tmp_path):
    db=tmp_path/'d.sqlite'
    _mk_db(db)
    o=DistanceOracle(db)
    assert o.distance('SemanticallyOddButNear','Target') == 3
    assert o.distance('Unknown','Target') is None
    assert o.batch_distance(['SemanticallyOddButNear','Unknown'],'Target') == {'SemanticallyOddButNear': 3, 'Unknown': None}
    assert o.batch_distance([], 'Target') == {}
    o.close()


class RankerPrefersFar:
    def rank(self, payload):
        return {'candidates': [{'page': 'SemanticallyCloseButFar', 'estimated_dist': 1}, {'page':'SemanticallyOddButNear','estimated_dist':1}]}


def test_fullstrategy_oracle_overrides_llm(tmp_path):
    db=tmp_path/'d.sqlite'
    _mk_db(db)
    o=DistanceOracle(db)
    s=FullStrategy(model=RankerPrefersFar(), adapter=None, top_k=5, deterministic_fallback=False, strategic_model=None, oracle=o)
    state=initialize_state('Start','Target',30)
    move,_=s.select_move(state,['SemanticallyCloseButFar','SemanticallyOddButNear'])
    assert move == 'SemanticallyOddButNear'
    o.close()


def test_fullstrategy_fallback_to_llm_when_oracle_miss():
    s=FullStrategy(model=RankerPrefersFar(), adapter=None, top_k=5, deterministic_fallback=False, strategic_model=None, oracle=None)
    state=initialize_state('Start','Target',30)
    move,_=s.select_move(state,['SemanticallyCloseButFar','SemanticallyOddButNear'])
    assert move == 'SemanticallyCloseButFar'
