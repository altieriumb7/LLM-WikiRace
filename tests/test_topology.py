from pathlib import Path
import re

def test_agent_has_no_mode_branching():
    src=Path('src/wikirace/agent.py').read_text()
    forbidden=['mode ==','mode_name','config.strategy','"baseline"','"state_only"','"stratified"','"full"','BaselineStrategy','StatefulStrategy','StratifiedStrategy','FullStrategy']
    for x in forbidden: assert x not in src
    assert re.search(r'from\s+\.tactical',src) is None
    assert re.search(r'from\s+\.strategic',src) is None
    assert re.search(r'from\s+\.replan',src) is None
    assert re.search(r'from\s+\.escape',src) is None
    assert re.search(r'from\s+\.fallback',src) is None
