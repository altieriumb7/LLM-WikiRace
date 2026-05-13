import json

from wikirace.demo_benchmark import compute_summary, load_cases, write_demo_benchmark


CASES = "benchmarks/qualitative_wikirace_cases.yaml"


def test_benchmark_cases_load():
    cases = load_cases(CASES)
    assert len(cases) >= 5
    assert {c.status for c in cases} <= {"pass", "fail", "warning"}


def test_summary_metrics():
    summary = compute_summary(load_cases(CASES))
    assert summary["total_cases"] == 6
    assert summary["pass_count"] == 5
    assert summary["warning_count"] == 1
    assert summary["pass_rate"] == 0.8333


def test_demo_benchmark_generation_is_deterministic(tmp_path):
    out1 = tmp_path / "one"
    out2 = tmp_path / "two"
    write_demo_benchmark(CASES, out1)
    write_demo_benchmark(CASES, out2)
    assert (out1 / "demo_results.json").read_text() == (out2 / "demo_results.json").read_text()


def test_reports_written_to_configured_dir(tmp_path):
    paths = write_demo_benchmark(CASES, tmp_path)
    assert paths["json"].exists()
    assert paths["csv"].exists()
    assert paths["markdown"].exists()
    data = json.loads(paths["json"].read_text())
    assert data["summary"]["is_demo"] is True
