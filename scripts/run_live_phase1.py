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
