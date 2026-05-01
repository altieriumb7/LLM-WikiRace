from pathlib import Path
import re

ACTIVE_RUNNERS=['scripts/run_phase2_ablations.py']


def test_runner_uses_generic_run_game_and_no_direct_components():
    banned_patterns=[r'from\s+wikirace\.invariant_gate',r'from\s+wikirace\.fallback',r'from\s+wikirace\.replan',r'from\s+wikirace\.tactical_model',r'from\s+wikirace\.strategic_model']
    for f in ACTIVE_RUNNERS:
        txt=Path(f).read_text()
        assert 'run_game(' in txt
        for pat in banned_patterns:
            assert re.search(pat, txt) is None
        assert 'if mode ==' not in txt and 'if mode_name ==' not in txt
