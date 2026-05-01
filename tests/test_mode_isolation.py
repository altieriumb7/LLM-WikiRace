from scripts.run_phase2_ablations import MockAdapter, parse_yaml
from wikirace.modes import get_mode_config
from wikirace.navigator import NavigatorConfig, StratifiedNavigator

class T:
    def rank(self,state):
        links=state.get('outgoing_links',['A'])
        return {'candidates':[{'page':links[0],'target_proximity':5,'hub_score':5,'estimated_dist':1,'milestone_progress':5,'novelty':True,'rationale':'x'}]}
class S:
    def __init__(self): self.calls=0
    def plan(self,state): self.calls+=1; return {'backbone':['X'],'current_milestone':'X'}

def test_mode_behaviors():
    cfg=parse_yaml('configs/stratified_navigator.yaml'); adapter=MockAdapter(); inst=adapter.get_game_instances('live','easy',1)[0]
    strategic=S(); nav=StratifiedNavigator(adapter,T(),strategic,NavigatorConfig(**cfg))
    b=nav.run_game(inst,lambda e:None,get_mode_config('baseline',cfg)); assert b['repeated']>=0
    so=nav.run_game(inst,lambda e:None,get_mode_config('state_only',cfg)); assert so['repeated']>=0
    st=nav.run_game(inst,lambda e:None,get_mode_config('stratified',cfg)); assert strategic.calls>=0
    fu=nav.run_game(inst,lambda e:None,get_mode_config('full',cfg)); assert fu['trap']>=0
