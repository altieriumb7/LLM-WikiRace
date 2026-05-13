from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from wikirace.config import ConfigValidationError, load_mode
from wikirace.demo_benchmark import compute_summary, load_cases, load_demo_report, write_demo_benchmark


DEFAULT_CASES = ROOT / "benchmarks" / "qualitative_wikirace_cases.yaml"


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_runtime_settings() -> dict[str, object]:
    return {
        "demo_mode": env_bool("DEMO_MODE", True),
        "allow_live_runs": env_bool("ALLOW_LIVE_RUNS", False),
        "openai_key_present": bool(os.getenv("OPENAI_API_KEY")),
        "default_config_path": os.getenv("DEFAULT_CONFIG_PATH", "evals/config.yaml"),
        "reports_dir": os.getenv("REPORTS_DIR", "reports"),
        "benchmark_mode": os.getenv("BENCHMARK_MODE", "demo"),
    }


def discover_configs(default_config: str) -> list[str]:
    candidates = [Path(default_config), *Path("evals").glob("*.yaml"), *Path("configs/modes").glob("*.yaml")]
    seen: list[str] = []
    for path in candidates:
        value = path.as_posix()
        if path.exists() and value not in seen:
            seen.append(value)
    return seen


def ensure_demo_report(reports_dir: str) -> Path:
    report_dir = Path(reports_dir) / "demo_benchmark"
    if not (report_dir / "demo_results.json").exists():
        write_demo_benchmark(DEFAULT_CASES, report_dir)
    return report_dir


def render_settings(settings: dict[str, object], selected_config: str, selected_report: str) -> None:
    mode = "demo" if settings["demo_mode"] else "live"
    st.sidebar.header("Runtime Settings")
    st.sidebar.write(f"Current mode: `{mode}`")
    st.sidebar.write(f"DEMO_MODE: `{settings['demo_mode']}`")
    st.sidebar.write(f"ALLOW_LIVE_RUNS: `{settings['allow_live_runs']}`")
    st.sidebar.write(f"OPENAI_API_KEY present: `{settings['openai_key_present']}`")
    st.sidebar.write(f"DEFAULT_CONFIG_PATH: `{settings['default_config_path']}`")
    st.sidebar.write(f"REPORTS_DIR: `{settings['reports_dir']}`")
    st.sidebar.write(f"Selected config: `{selected_config}`")
    st.sidebar.write(f"Selected report: `{selected_report}`")


def render_config_tab(selected_config: str) -> None:
    st.subheader("Selected Configuration")
    try:
        cfg = load_mode(Path(selected_config))
        st.success("Config loaded successfully.")
        st.json(cfg.__dict__)
    except (ConfigValidationError, FileNotFoundError, TypeError) as exc:
        st.error(f"Config could not be loaded: {exc}")


def render_benchmark_tab(settings: dict[str, object], report_dir: Path) -> None:
    if settings["demo_mode"]:
        st.info(
            "Public demo mode: live model calls are disabled. This demo uses sample benchmark reports. "
            "Clone the repo and set OPENAI_API_KEY to run full evaluations."
        )
    else:
        st.warning("Live mode is selected. Any live evaluation may consume API credits.")

    report = load_demo_report(report_dir)
    cases = load_cases(DEFAULT_CASES)
    summary = report.get("summary") or compute_summary(cases)
    rows = report.get("cases", [])
    df = pd.DataFrame(rows)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total", summary["total_cases"])
    c2.metric("Pass", summary["pass_count"])
    c3.metric("Warning", summary["warning_count"])
    c4.metric("Pass rate", f"{summary['pass_rate']:.0%}")

    st.subheader("Category Breakdown")
    if not df.empty:
        st.dataframe(df.groupby(["category", "status"]).size().reset_index(name="count"), use_container_width=True)

    st.subheader("Qualitative Case Gallery")
    for row in rows:
        label = f"{row['case_id']} · {row['category']} · {row['status']}"
        with st.expander(label):
            st.write("Input prompt")
            st.code(row["input_prompt"])
            st.write(f"Expected behavior: {row['expected_behavior']}")
            st.write(f"Observed/demo output: {row['observed_demo_output']}")
            st.write(f"Assessment: {row['qualitative_assessment']}")
            st.write(f"Notes: {row['notes']}")

    st.subheader("Failure/Error Examples")
    flagged = df[df["status"].isin(["fail", "warning"])] if not df.empty else pd.DataFrame()
    if flagged.empty:
        st.write("No failing demo cases. Warning cases, when present, are shown here.")
    else:
        st.dataframe(flagged[["case_id", "category", "status", "notes"]], use_container_width=True)

    json_path = report_dir / "demo_results.json"
    csv_path = report_dir / "demo_summary.csv"
    md_path = report_dir / "qualitative_case_gallery.md"
    st.download_button("Download JSON report", json_path.read_text(encoding="utf-8"), "demo_results.json")
    st.download_button("Download CSV summary", csv_path.read_text(encoding="utf-8"), "demo_summary.csv")
    st.download_button("Download Markdown report", md_path.read_text(encoding="utf-8"), "qualitative_case_gallery.md")

    st.caption("Hosted public demos use static deterministic reports. Live evaluation requires local credentials and explicit opt-in.")


def render_live_tab(settings: dict[str, object]) -> None:
    st.subheader("Live Evaluation")
    if settings["demo_mode"] or not settings["allow_live_runs"]:
        st.info("Live runs are disabled. Set DEMO_MODE=false and ALLOW_LIVE_RUNS=true in a private environment to enable them.")
        return
    session_key = st.text_input("Session-only OpenAI API key", type="password")
    key_available = bool(session_key or os.getenv("OPENAI_API_KEY"))
    if not key_available:
        st.warning("Provide an API key to run live evaluations. The dashboard does not persist session keys.")
        return
    st.warning("Live model/API usage may consume API credits. Use the CLI for full runs:")
    st.code("python scripts/run_phase2_ablations.py --real-models --difficulty hard --limit 100 --output-dir reports/live_TIMESTAMP")


def main() -> None:
    st.set_page_config(page_title="LLM WikiRace Evaluation Dashboard", layout="wide")
    settings = get_runtime_settings()
    configs = discover_configs(str(settings["default_config_path"]))
    selected_config = st.sidebar.selectbox("Config file", configs, index=0) if configs else str(settings["default_config_path"])
    report_dir = ensure_demo_report(str(settings["reports_dir"]))
    render_settings(settings, selected_config, report_dir.as_posix())

    st.title("LLM WikiRace Evaluation Dashboard")
    st.write("Safe public dashboard for qualitative WikiRace navigation evaluation artifacts.")

    tab_config, tab_benchmark, tab_live = st.tabs(["Configuration", "Benchmark & Qualitative Evaluation", "Live Runs"])
    with tab_config:
        render_config_tab(selected_config)
    with tab_benchmark:
        render_benchmark_tab(settings, report_dir)
    with tab_live:
        render_live_tab(settings)


if __name__ == "__main__":
    main()
