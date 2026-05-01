"""Test compatibility shim. Not used in the production execution path."""
from pathlib import Path
import json

from .agent import run_game
from .config import ModeConfig
from .strategies import build_strategy


def _parse_yaml(path: str) -> dict:
    data = {}
    for ln in Path(path).read_text().splitlines():
        s = ln.strip()
        if not s or s.startswith('#') or ':' not in s:
            continue
        k, v = s.split(':', 1)
        v = v.strip()
        if v in ('null', 'None'):
            val = None
        elif v in ('true', 'false'):
            val = (v == 'true')
        elif v.isdigit():
            val = int(v)
        elif v.startswith('['):
            val = json.loads(v.replace("'", '"'))
        else:
            val = v.strip('"')
        data[k.strip()] = val
    return data


def load_config(path: str):
    return _parse_yaml(path)


def mock_ranker(state):
    links = state.get('outgoing_links', [])
    candidates = []
    for i, p in enumerate(links):
        candidates.append({
            'page': p, 'target_proximity': max(1, 10-i), 'hub_score': 5, 'estimated_dist': 1,
            'milestone_progress': 5, 'novelty': p not in state.get('visited', []), 'rationale': 'mock', 'combined_score': 10-i,
        })
    return {'candidates': candidates}


def mock_planner(state):
    t = state.get('target_page', 'T')
    return {'backbone': [t], 'current_milestone': t, 'reasoning_summary': 'mock', 'escape_advice': 'none'}


class _Adapter:
    graph = {
        'Backpropagation': ['Neural network'],
        'Neural network': ['Biology'],
        'Biology': ['Photosynthesis'],
        'Photosynthesis': [],
    }

    def get_outgoing_links(self, page): return self.graph.get(page, [])
    def is_target(self, c, t): return c == t


def run_instances(instances, cfg, mode):
    mode_map = {
        'baseline': ModeConfig(strategy='baseline', model='mock'),
        'state_only': ModeConfig(strategy='state_only', model='mock', deterministic_fallback=True),
        'stratified': ModeConfig(strategy='stratified', tactical_model='mock', strategic_model='mock', deterministic_fallback=True),
        'full': ModeConfig(strategy='full', tactical_model='mock', strategic_model='mock', escape_threshold=10, deterministic_fallback=True),
        'full_stratified': ModeConfig(strategy='full', tactical_model='mock', strategic_model='mock', escape_threshold=10, deterministic_fallback=True),
    }
    adapter = _Adapter()
    strategy = build_strategy(mode_map.get(mode, mode_map['full_stratified']), adapter)
    rows = []
    for inst in instances:
        res = run_game(inst['start_page'], inst['target_page'], strategy, adapter)
        rows.append({'success': res['status'] == 'success', **res})
    return rows
