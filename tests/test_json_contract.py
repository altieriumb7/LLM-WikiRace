from wikirace.tactical_model import TacticalModel

class DummyAPI:
    def __init__(self, texts): self.texts=texts; self.i=0
    def complete_json(self,*a,**k):
        t=self.texts[self.i]; self.i+=1
        return type('R',(),{'text':t})

def test_valid_tactical_json_parses():
    m=TacticalModel(DummyAPI(['{"candidates":[{"page":"X","target_proximity":7,"hub_score":7,"estimated_dist":7,"milestone_progress":7,"novelty":true,"rationale":"ok"}]}']),'x')
    assert m.rank({})['candidates'][0]['page']=='X'

def test_markdown_fenced_json_parses():
    m=TacticalModel(DummyAPI(['```json\n{"candidates":[{"page":"X","target_proximity":7,"hub_score":7,"estimated_dist":7,"milestone_progress":7,"novelty":true,"rationale":"ok"}]}\n```']),'x')
    assert m.rank({})['failure_reason'] is None

def test_malformed_repair_once_then_fallback_marker():
    m=TacticalModel(DummyAPI(['bad','still bad']),'x')
    out=m.rank({})
    assert out['failure_reason']=='schema_repair_failed'
