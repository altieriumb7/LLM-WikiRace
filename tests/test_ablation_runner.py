import json, tempfile
from pathlib import Path
from scripts.run_phase2_ablations import main
import sys


def test_runner_outputs():
    with tempfile.TemporaryDirectory() as d:
        sys.argv=['x','--difficulty','easy','--limit','2','--output-dir',d,'--mock']
        main()
        root=max(Path(d).iterdir(), key=lambda p:p.stat().st_mtime)
        assert (root/'instances.jsonl').exists()
        for m in ['baseline','state_only','stratified','full']:
            assert (root/m/'results.jsonl').exists()
        s=json.loads((root/'summary.json').read_text())
        assert all(m in s for m in ['baseline','state_only','stratified','full'])
