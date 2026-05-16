from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    category: str
    input_prompt: str
    expected_behavior: str
    observed_demo_output: str
    qualitative_assessment: str
    status: str
    notes: str


def load_cases(path: str | Path) -> list[BenchmarkCase]:
    data = yaml.safe_load(Path(path).read_text()) or {}
    raw_cases = data.get("cases", [])
    if not isinstance(raw_cases, list):
        raise ValueError("benchmark cases file must contain a cases list")
    cases = [BenchmarkCase(**case) for case in raw_cases]
    bad = [case.case_id for case in cases if case.status not in {"pass", "fail", "warning"}]
    if bad:
        raise ValueError(f"invalid benchmark status for cases: {bad}")
    return cases


def compute_summary(cases: list[BenchmarkCase]) -> dict[str, Any]:
    total = len(cases)
    pass_count = sum(1 for c in cases if c.status == "pass")
    fail_count = sum(1 for c in cases if c.status == "fail")
    warning_count = sum(1 for c in cases if c.status == "warning")
    non_fail_count = pass_count + warning_count
    categories = sorted({c.category for c in cases})
    return {
        "mode": "demo",
        "total_cases": total,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "warning_count": warning_count,
        "non_fail_count": non_fail_count,
        "pass_rate": round(pass_count / total, 4) if total else 0.0,
        "non_fail_rate": round(non_fail_count / total, 4) if total else 0.0,
        "categories_covered": categories,
        "is_demo": True,
    }


def compute_category_summary(cases: list[BenchmarkCase]) -> list[dict[str, Any]]:
    rows = []
    for category in sorted({case.category for case in cases}):
        subset = [case for case in cases if case.category == category]
        total = len(subset)
        pass_count = sum(1 for case in subset if case.status == "pass")
        warning_count = sum(1 for case in subset if case.status == "warning")
        fail_count = sum(1 for case in subset if case.status == "fail")
        rows.append(
            {
                "category": category,
                "total_cases": total,
                "pass_count": pass_count,
                "warning_count": warning_count,
                "fail_count": fail_count,
                "pass_rate": round(pass_count / total, 4) if total else 0.0,
                "non_fail_rate": round((pass_count + warning_count) / total, 4) if total else 0.0,
            }
        )
    return rows


def cases_to_rows(cases: list[BenchmarkCase]) -> list[dict[str, str]]:
    return [case.__dict__.copy() for case in cases]


def render_gallery_markdown(cases: list[BenchmarkCase], summary: dict[str, Any]) -> str:
    lines = [
        "# Demo Qualitative Benchmark Gallery",
        "",
        "These are deterministic sample results for the public demo. They do not claim live model performance.",
        "",
        f"- Total cases: {summary['total_cases']}",
        f"- Pass: {summary['pass_count']}",
        f"- Warning: {summary['warning_count']}",
        f"- Fail: {summary['fail_count']}",
        f"- Pass rate: {summary['pass_rate']:.0%}",
        f"- Non-failing rate: {summary['non_fail_rate']:.0%}",
        "",
    ]
    for case in cases:
        lines.extend(
            [
                f"## {case.case_id}: {case.category}",
                "",
                f"- Status: {case.status}",
                f"- Input: {case.input_prompt}",
                f"- Expected: {case.expected_behavior}",
                f"- Observed demo output: {case.observed_demo_output}",
                f"- Assessment: {case.qualitative_assessment}",
                f"- Notes: {case.notes}",
                "",
            ]
        )
    return "\n".join(lines)


def write_demo_benchmark(cases_path: str | Path, output_dir: str | Path) -> dict[str, Path]:
    cases = load_cases(cases_path)
    summary = compute_summary(cases)
    rows = cases_to_rows(cases)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    results_path = out / "demo_results.json"
    csv_path = out / "demo_summary.csv"
    gallery_path = out / "qualitative_case_gallery.md"

    results_path.write_text(json.dumps({"summary": summary, "cases": rows}, indent=2), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
        writer.writeheader()
        writer.writerows(rows)
    gallery_path.write_text(render_gallery_markdown(cases, summary), encoding="utf-8")
    return {"json": results_path, "csv": csv_path, "markdown": gallery_path}


def load_demo_report(report_dir: str | Path) -> dict[str, Any]:
    path = Path(report_dir) / "demo_results.json"
    if not path.exists():
        raise FileNotFoundError(f"demo report not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))
