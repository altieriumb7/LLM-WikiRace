import json
import tempfile
from pathlib import Path
import sys

from scripts.run_phase2_ablations import main


def test_flat_jsonl_schema_has_controller_counts():
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "mock_schema_check.jsonl"
        sys.argv = [
            "x", "--mode", "configs/modes/full.yaml", "--games", "2", "--difficulty", "hard", "--output", str(out), "--mock"
        ]
        main()
        rows = [json.loads(l) for l in out.read_text().splitlines() if l.strip()]

        required_fields = {
            "start", "target", "status", "steps_used", "path", "failure_reason",
            "replan_count", "escape_count", "trap_count", "fallback_used_count",
        }
        for row in rows:
            assert required_fields.issubset(row.keys())
            assert isinstance(row["path"], list)
            for key in ["replan_count", "escape_count", "trap_count", "fallback_used_count"]:
                assert isinstance(row[key], int)
                assert row[key] >= 0
