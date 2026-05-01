#!/usr/bin/env python
import sys, argparse, json, uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from wikirace.agent import run_game
from wikirace.api_client import FrontierAPIClient
from wikirace.live_adapter import WikiRaceAdapter
from wikirace.strategies import build_strategy_with_models
from scripts.run_phase2_ablations import parse_yaml


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--difficulty'); ap.add_argument('--limit',type=int); ap.add_argument('--config',required=True); ap.add_argument('--output-dir'); ap.add_argument('--resume')
    args=ap.parse_args(); cfg=parse_yaml(args.config)
    run_id=str(uuid.uuid4()); out=Path(args.output_dir or 'outputs/live_phase1')/run_id; out.mkdir(parents=True,exist_ok=True)
    adapter=WikiRaceAdapter(max_retries=int(cfg.get('max_api_retries',5)), backoff_initial_seconds=int(cfg.get('api_backoff_initial_seconds',1)), backoff_max_seconds=int(cfg.get('api_backoff_max_seconds',30)) )
    instances=adapter.get_game_instances('live',args.difficulty,args.limit)
    api=FrontierAPIClient(); strategy=build_strategy_with_models('full',cfg,api,adapter,mock=False)
    summary={'num_games':len(instances),'successes':0,'failures':0,'failure_reasons':{}}
    for inst in instances:
        res=run_game(inst,adapter,strategy,budget=int(cfg.get('budget',30)),logger=lambda e: None)
        if res['status']=='success': summary['successes']+=1
        else:
            summary['failures']+=1; fr=res.get('failure_reason','unknown'); summary['failure_reasons'][fr]=summary['failure_reasons'].get(fr,0)+1
        with (out/'games.jsonl').open('a') as f:f.write(json.dumps({'instance_id':inst.instance_id,'result':res['status'],'failure_reason':res.get('failure_reason')})+'\n')
    summary['success_rate']=summary['successes']/summary['num_games'] if summary['num_games'] else 0
    (out/'summary.json').write_text(json.dumps(summary,indent=2))

if __name__=='__main__': main()
