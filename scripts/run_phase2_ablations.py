#!/usr/bin/env python
import sys,argparse,json,uuid,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from wikirace.agent import run_game
from wikirace.adapter import WikiRaceAdapter
from wikirace.config import load_mode
from wikirace.strategies import build_strategy

class MockAdapter:
    graph={'A':['B','C'],'B':['A','D'],'C':['D'],'D':['T'],'T':[]}
    def get_instances(self,difficulty,limit): return [{'instance_id':f'{difficulty}-{i}','start_page':'A','target_page':'T','difficulty':difficulty} for i in range(limit)]
    def get_game_instances(self, split, difficulty, limit):
        class GI:
            def __init__(self, d):
                self.instance_id=d['instance_id']; self.start_page=d['start_page']; self.target_page=d['target_page']; self.difficulty=d['difficulty']
        return [GI(x) for x in self.get_instances(difficulty, limit)]
    def get_outgoing_links(self,page): return self.graph.get(page,[])
    def is_target(self,c,t): return c==t

def default_mode_paths():
    return [Path('configs/modes/baseline.yaml'),Path('configs/modes/state_only.yaml'),Path('configs/modes/stratified.yaml'),Path('configs/modes/full.yaml')]


def parse_value(v):
    v=v.strip()
    if v in ("true","false"): return v=="true"
    if v in ("null", "None"): return None
    if v.startswith("["): return json.loads(v.replace("'",'"'))
    vv=v.strip('"')
    return int(vv) if vv.isdigit() else vv


def parse_yaml(path):
    data={}
    for raw in Path(path).read_text().splitlines():
        if not raw.strip() or raw.strip().startswith('#') or ':' not in raw:
            continue
        k,v=raw.split(':',1)
        data[k.strip()] = parse_value(v)
    return data

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--difficulty',default='easy'); ap.add_argument('--limit','--games',dest='limit',type=int,default=1); ap.add_argument('--mode-configs','--mode',dest='mode_configs',nargs='*'); ap.add_argument('--output-dir','--output',dest='output_dir',default='outputs/phase2_ablations'); ap.add_argument('--mock',action='store_true'); ap.add_argument('--dry-run',action='store_true')
    args=ap.parse_args(); paths=[Path(p) for p in (args.mode_configs or default_mode_paths())]
    modes=[load_mode(p) for p in paths]
    if args.dry_run:
        print('validated', [m.strategy for m in modes]); return
    use_mock = args.mock or os.getenv('WIKIRACE_MOCK') == '1'
    adapter=MockAdapter() if use_mock else WikiRaceAdapter()
    instances=adapter.get_instances(args.difficulty,args.limit)

    # Flat JSONL mode when output points to a file path.
    if str(args.output_dir).endswith('.jsonl') and len(modes) == 1:
        out_file = Path(args.output_dir)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        strategy=build_strategy(modes[0],adapter)
        rows=[]
        for inst in instances:
            r=run_game(inst['start_page'],inst['target_page'],strategy,adapter,budget=modes[0].budget)
            st=r.get('state')
            rows.append({
                'start': inst['start_page'],
                'target': inst['target_page'],
                'steps_used': getattr(st, 'steps_used', None),
                'status': r.get('status'),
                'path': list(getattr(st, 'path', [])),
                'failure_reason': r.get('failure_reason'),
                'final_page': getattr(st, 'current_page', None),
                'repeated_page_attempts': r.get('repeated_page_attempts', 0),
                'budget_rejections': r.get('budget_rejections', 0),
                'schema_violations': r.get('schema_violations', 0),
                'trap_detections': r.get('trap_detections', 0),
                'strategic_replans': r.get('strategic_replans', 0),
                'fallback_used': r.get('fallback_used', 0),
                'api_errors': r.get('api_errors', 0),
            })
        out_file.write_text('\n'.join(json.dumps(x) for x in rows)+'\n')
        return

    run_id=str(uuid.uuid4()); out=Path(args.output_dir)/run_id; out.mkdir(parents=True,exist_ok=True)
    (out/'instances.jsonl').write_text('\n'.join(json.dumps(i) for i in instances)+'\n')
    summary={}
    for m in modes:
        strategy=build_strategy(m,adapter)
        mdir=out/m.strategy; mdir.mkdir(exist_ok=True)
        rows=[]
        for inst in instances:
            r=run_game(inst['start_page'],inst['target_page'],strategy,adapter,budget=m.budget)
            row={'mode':m.strategy,'instance_id':inst['instance_id'],**r}
            row.pop('state', None)
            rows.append(row)
        (mdir/'results.jsonl').write_text('\n'.join(json.dumps(r) for r in rows)+'\n')
        summary[m.strategy]={'num_instances':len(rows),'successes':sum(1 for r in rows if r['status']=="success")}
    (out/'summary.json').write_text(json.dumps(summary,indent=2))



if __name__ == '__main__':
    main()
