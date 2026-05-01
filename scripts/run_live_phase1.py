#!/usr/bin/env python
import sys,argparse,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from wikirace.agent import run_game
from wikirace.adapter import WikiRaceAdapter
from wikirace.config import load_config, strategy_from_mode
from wikirace.strategies import build_strategy
from scripts.run_phase2_ablations import MockModel

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--difficulty'); ap.add_argument('--limit',type=int); ap.add_argument('--config',required=True); ap.add_argument('--output-dir',required=True)
    args=ap.parse_args(); cfg=load_config(args.config); adapter=WikiRaceAdapter(); mode=strategy_from_mode('full',cfg); strategy=build_strategy(mode,MockModel(),MockModel(),adapter)
    out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)
    for inst in adapter.get_instances(args.difficulty,args.limit):
        r=run_game(inst['start_page'],inst['target_page'],strategy,adapter,budget=cfg.budget)
        with (out/'games.jsonl').open('a') as f:f.write(json.dumps({'id':inst['instance_id'],**r.to_dict()})+'\n')
if __name__=='__main__': main()
import sys
from pathlib import Path as _P
sys.path.insert(0,str(_P(__file__).resolve().parents[1]/"src"))
#!/usr/bin/env python
import argparse, json, uuid
from pathlib import Path
from wikirace.api_client import FrontierAPIClient
from wikirace.live_adapter import WikiRaceAdapter
from wikirace.navigator import NavigatorConfig, StratifiedNavigator
from wikirace.session import save_checkpoint, load_checkpoint
from wikirace.strategic_model import StrategicModel
from wikirace.tactical_model import TacticalModel


def parse_cfg(path):
    data={}
    for ln in Path(path).read_text().splitlines():
        if ':' in ln and not ln.strip().startswith('#'):
            k,v=ln.split(':',1);data[k.strip()]=v.strip().strip('"')
    ints={"budget","top_k","beam_width","trap_target_score_threshold","escape_resolved_outdegree_threshold","max_api_retries","api_backoff_initial_seconds","api_backoff_max_seconds"}
    for k in list(data):
        if k in ints:data[k]=int(data[k])
    return data


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--difficulty')
    ap.add_argument('--limit',type=int)
    ap.add_argument('--config')
    ap.add_argument('--output-dir')
    ap.add_argument('--resume')
    args=ap.parse_args()

    if args.resume:
        ck=load_checkpoint(args.resume)
        run_id=ck['run_id']; output_dir=Path(args.resume).parent
    else:
        cfg=parse_cfg(args.config); run_id=str(uuid.uuid4()); output_dir=Path(args.output_dir)/run_id; output_dir.mkdir(parents=True,exist_ok=True)
        adapter=WikiRaceAdapter(max_retries=cfg.get('max_api_retries',5), backoff_initial_seconds=cfg.get('api_backoff_initial_seconds',1), backoff_max_seconds=cfg.get('api_backoff_max_seconds',30))
        instances=adapter.get_game_instances('live',args.difficulty,args.limit)
        ck={"run_id":run_id,"index":0,"instances":[i.__dict__ for i in instances],"summary":{"num_games":len(instances),"successes":0,"failures":0,"failure_reasons":{},"total_schema_violations":0,"total_loop_attempts":0,"total_api_errors":0}}

    cfg=parse_cfg(args.config) if not args.resume else parse_cfg('configs/stratified_navigator.yaml')
    api=FrontierAPIClient(); tactical=TacticalModel(api,cfg.get('tactical_model','gpt-4o-mini'),top_k=cfg.get('top_k',5)); strategic=StrategicModel(api,cfg.get('strategic_model','gpt-4o'))
    adapter=WikiRaceAdapter(max_retries=cfg.get('max_api_retries',5), backoff_initial_seconds=cfg.get('api_backoff_initial_seconds',1), backoff_max_seconds=cfg.get('api_backoff_max_seconds',30))
    nav=StratifiedNavigator(adapter,tactical,strategic,NavigatorConfig(**cfg))

    def logger(ev):
        with (output_dir/'events.jsonl').open('a') as f:f.write(json.dumps(ev)+'\n')

    for idx in range(ck['index'], len(ck['instances'])):
        inst=type('I',(),ck['instances'][idx])
        res=nav.run_game(inst,logger)
        with (output_dir/'games.jsonl').open('a') as f:f.write(json.dumps({"instance_id":inst.instance_id, "difficulty":inst.difficulty, "result":res['status'], "failure_reason":res.get('failure_reason')})+'\n')
        if res['status']=='success': ck['summary']['successes']+=1
        else:
            ck['summary']['failures']+=1
            fr=res.get('failure_reason','unknown'); ck['summary']['failure_reasons'][fr]=ck['summary']['failure_reasons'].get(fr,0)+1
        ck['index']=idx+1
        save_checkpoint(str(output_dir/'checkpoint.json'), ck)
    s=ck['summary']; s['success_rate']=s['successes']/s['num_games'] if s['num_games'] else 0
    (output_dir/'summary.json').write_text(json.dumps(s,indent=2))

if __name__=='__main__':main()
