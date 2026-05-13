#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Directory containing benchmark json/jsonl outputs")
    ap.add_argument("--output", default="benchmark_summary.json")
    args = ap.parse_args()

    root = Path(args.input)
    rows = []
    for p in list(root.rglob("*.jsonl")) + list(root.rglob("*.json")):
        try:
            if p.suffix == ".jsonl":
                for line in p.read_text().splitlines():
                    if line.strip():
                        rows.append(json.loads(line))
            else:
                obj = json.loads(p.read_text())
                if isinstance(obj, list):
                    rows.extend(obj)
                elif isinstance(obj, dict):
                    rows.append(obj)
        except Exception:
            continue

    total = len(rows)
    success = sum(1 for r in rows if str(r.get("status", "")).lower() == "success")
    failed = total - success
    by_reason = {}
    for r in rows:
        if str(r.get("status", "")).lower() == "success":
            continue
        reason = r.get("failure_reason", "unknown")
        by_reason[reason] = by_reason.get(reason, 0) + 1

    summary = {
        "total": total,
        "success": success,
        "failed": failed,
        "success_rate": (success / total) if total else 0.0,
        "failure_reasons": by_reason,
    }
    Path(args.output).write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
