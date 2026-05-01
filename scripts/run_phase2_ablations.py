#!/usr/bin/env python
import sys, json, argparse, uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from wikirace.api_client import FrontierAPIClient
from wikirace.live_adapter import WikiRaceAdapter, GameInstance, PageMetrics
from wikirace.modes import get_mode_config
from wikirace.navigator import NavigatorConfig, StratifiedNavigator
from wikirace.results import AblationResult, summarize_mode
from wikirace.strategic_model import StrategicModel
from wikirace.tactical_model import TacticalModel

def parse_value(v):
    v=v.strip()
    if v in ('true','false'): return v=='true'
    if v=='null': return None
    if v.startswith('['): return json.loads(v.replace("'",'"'))
    vv=v.strip('"')
    return int(vv) if vv.isdigit() else vv

def parse_yaml(path):
    root={}; modes={}; current=None
    for raw in Path(path).read_text().splitlines():
        if not raw.strip() or raw.strip().startswith('#'): continue
        indent=len(raw)-len(raw.lstrip(' ')); s=raw.strip()
        if s=='modes:': root['modes']=modes; continue
        if indent==2 and s.endswith(':') and s[:-1] in ['baseline','state_only','stratified','full']:
            current=s[:-1]; modes[current]={}; continue
        if ':' in s:
            k,v=s.split(':',1)
            if current and indent>=4: modes[current][k]=parse_value(v)
            elif indent==0: root[k]=parse_value(v)
    return root

class MockAdapter:
    def __init__(self): self.graph={"A":["B","C"],"B":["A","D"],"C":["D"],"D":["T"],"T":[]}
    def get_game_instances(self, split,difficulty,limit): return [GameInstance(instance_id=f"{difficulty}-{i}",start_page='A',target_page='T',difficulty=difficulty) for i in range(limit)]
    def get_outgoing_links(self,page): return self.graph.get(page,[])
    def get_page_metrics(self,page): return PageMetrics(page=page,out_degree=len(self.get_outgoing_links(page)),pagerank=None)
    def get_link_metrics(self,pages): return {p:self.get_page_metrics(p) for p in pages}
    def is_target(self,c,t): return c==t

class MockTactical:
    def rank(self,state):
        links=state.get('outgoing_links',[])
        c=[{"page":p,"target_proximity":max(1,10-i),"hub_score":5,"estimated_dist":1,"milestone_progress":5,"novelty":True,"rationale":"mock"} for i,p in enumerate(links)]
        return {"candidates":c}
class MockStrategic:
    def plan(self,state): return {"backbone":["X","Y"],"current_milestone":"X"}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--difficulty',required=True); ap.add_argument('--limit',type=int); ap.add_argument('--limit-per-difficulty',type=int); ap.add_argument('--modes',required=True); ap.add_argument('--config',required=True); ap.add_argument('--output-dir',required=True); ap.add_argument('--mock',action='store_true'); args=ap.parse_args()
    cfg=parse_yaml(args.config); run_id=str(uuid.uuid4()); out=Path(args.output_dir)/run_id; out.mkdir(parents=True,exist_ok=True)
    diffs=['easy','medium','hard'] if args.difficulty=='all' else [args.difficulty]; lim=args.limit or args.limit_per_difficulty or 1
    adapter=MockAdapter() if args.mock else WikiRaceAdapter(max_retries=int(cfg.get('max_api_retries',5)), backoff_initial_seconds=int(cfg.get('api_backoff_initial_seconds',1)), backoff_max_seconds=int(cfg.get('api_backoff_max_seconds',30)))
    instances=[]
    for d in diffs: instances.extend(adapter.get_game_instances('live',d,lim))
    (out/'instances.jsonl').write_text('\n'.join(json.dumps(i.__dict__) for i in instances)+'\n'); (out/'config_resolved.yaml').write_text(Path(args.config).read_text())
    results_by_mode={}
    for mode_name in args.modes.split(','):
        mode=get_mode_config(mode_name,cfg); mdir=out/mode_name; mdir.mkdir(exist_ok=True)
        if args.mock: tactical,strategic=MockTactical(),MockStrategic()
        else:
            api=FrontierAPIClient(); tactical=TacticalModel(api,mode.tactical_model,top_k=mode.top_k); strategic=StrategicModel(api,mode.strategic_model or mode.tactical_model)
        nav=StratifiedNavigator(adapter,tactical,strategic,NavigatorConfig(**cfg)); rows=[]
        for inst in instances:
            res=nav.run_game(inst,lambda e: None,mode)
            rows.append(AblationResult(run_id,mode_name,inst.instance_id,inst.difficulty,inst.start_page,inst.target_page,res['status']=='success',res['state'].steps_used,list(res['state'].path),res.get('failure_reason'),res.get('repeated',0),res.get('budget_rejections',0),res.get('schema_violations',0),res.get('trap',0),res.get('replans',0),res.get('fallback',0),res.get('api_errors',0)))
        (mdir/'results.jsonl').write_text('\n'.join(json.dumps(r.__dict__) for r in rows)+'\n'); results_by_mode[mode_name]=rows
    summary={m:summarize_mode(r) for m,r in results_by_mode.items()}; summary['is_mock']=args.mock
    (out/'summary.json').write_text(json.dumps(summary,indent=2)); (out/'run_manifest.json').write_text(json.dumps({"run_id":run_id,"modes":args.modes.split(','),"difficulty":args.difficulty,"limit":lim,"is_mock":args.mock},indent=2))
if __name__=='__main__': main()
