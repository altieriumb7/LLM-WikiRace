#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from wikirace.oracle import DistanceOracle


def load_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--oracle", default="data/oracle.db")
    parser.add_argument("--instances", default="data/hard_instances.jsonl")
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()

    oracle = DistanceOracle(args.oracle)
    instances = load_jsonl(Path(args.instances))[: args.limit]

    exact_hits = 0
    missing = []

    for inst in instances:
        start = inst["start"]
        target = inst["target"]
        d = oracle.distance(start, target)

        if d is not None:
            exact_hits += 1
        else:
            missing.append((start, target))

    total = len(instances)
    rate = exact_hits / total * 100 if total else 0.0

    print(f"Instances checked: {total}")
    print(f"Exact pair coverage: {exact_hits}/{total} ({rate:.1f}%)")

    if missing[:10]:
        print("First missing pairs:")
        for start, target in missing[:10]:
            print(f"  {start} -> {target}")

    oracle.close()


if __name__ == "__main__":
    main()
