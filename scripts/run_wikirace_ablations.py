#!/usr/bin/env python
import argparse
import json
from pathlib import Path

from wikirace.experiments import load_config, run_instances
from wikirace.metrics import summarize


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instances", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    instances = [json.loads(x) for x in Path(args.instances).read_text().splitlines() if x.strip()]
    cfg = load_config(args.config)
    modes = ["baseline_chat", "json_state_only", "tactical_strategic", "full_stratified"]
    all_rows = []
    for m in modes:
        rows = run_instances(instances, cfg, m)
        all_rows.extend(rows)

    outp = Path(args.output)
    outp.parent.mkdir(parents=True, exist_ok=True)
    with outp.open("w", encoding="utf-8") as f:
        for row in all_rows:
            f.write(json.dumps(row) + "\n")

    summary = summarize(all_rows)
    Path("outputs/summary.csv").write_text("metric,value\n" + "\n".join(f"{k},{v}" for k, v in summary.items()))
    Path("outputs/summary.md").write_text("# Summary\n\n" + "\n".join(f"- {k}: {v}" for k, v in summary.items()))
    Path("outputs/failure_analysis.md").write_text("# Failure analysis\n\nMock-graph structural validation only.")


if __name__ == "__main__":
    main()
