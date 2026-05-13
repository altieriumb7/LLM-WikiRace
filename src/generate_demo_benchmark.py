from __future__ import annotations

import argparse

from .wikirace.demo_benchmark import write_demo_benchmark


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", default="benchmarks/qualitative_wikirace_cases.yaml")
    parser.add_argument("--output", default="reports/demo_benchmark")
    args = parser.parse_args()
    paths = write_demo_benchmark(args.cases, args.output)
    for kind, path in paths.items():
        print(f"{kind}: {path}")


if __name__ == "__main__":
    main()
