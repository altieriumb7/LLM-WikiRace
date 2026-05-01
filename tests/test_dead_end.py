from wikirace.agent import run_game
from wikirace.config import ModeConfig
from wikirace.strategies import build_strategy

class A:
    def __init__(self): self.i=0
    def get_outgoing_links(self,page):
        self.i+=1
        return [] if self.i>=5 else ['A']
    def is_target(self,c,t): return False

def test_dead_end_result():
    a=A(); s=build_strategy(ModeConfig(strategy='baseline',model='x'),a)
    r=run_game('S','T',s,a,budget=30)
    assert (r.success is False) and (r.failure_reason=='dead_end')
