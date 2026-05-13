# An Open and Deployable Dashboard for LLM WikiRace Navigation Evaluation

## Abstract

This report describes a deployable Python and Streamlit dashboard for inspecting LLM-guided WikiRace navigation strategies. The repository provides a CLI evaluator, mode configurations, deterministic demo benchmark artifacts, and Hugging Face Spaces deployment support. The public dashboard runs safely without API keys by default and uses static demo reports under `reports/demo_benchmark`. Live evaluation remains available through local CLI commands when a user supplies the required credentials and endpoint configuration.

## 1. Introduction

LLM evaluation tools are most useful when their behavior is visible, reproducible, and safe to demonstrate publicly. This project focuses on WikiRace navigation: choosing links from a start page toward a target page under constraints such as budget, cycle avoidance, fallback behavior, and optional model-backed ranking. The deployed demo is intended for portfolio review and qualitative inspection, not as a claim of benchmark superiority.

## 2. System Overview

The system has two execution surfaces:

| Surface | Entrypoint | Purpose |
|---|---|---|
| Streamlit dashboard | `app.py` | Public demo, config inspection, qualitative benchmark display |
| CLI evaluator | `scripts/run_phase2_ablations.py` | Mock, live deterministic, and optional OpenAI-backed WikiRace runs |
| Demo benchmark generator | `python -m src.generate_demo_benchmark` | Deterministic static reports for public hosting |
| Official benchmark bridge | `scripts/run_benchmark_batch_eval.py` | Optional integration requiring `LLM_wikirace` |

Core implementation lives in `src/wikirace`, with mode configs in `configs/modes` and the Hugging Face default config in `evals/config.yaml`.

## 3. Architecture

The dashboard reads environment variables through helper functions in `app.py`:

- `DEMO_MODE`
- `ALLOW_LIVE_RUNS`
- `OPENAI_API_KEY`
- `DEFAULT_CONFIG_PATH`
- `REPORTS_DIR`
- `BENCHMARK_MODE`

The benchmark layer is implemented in `src/wikirace/demo_benchmark.py`. It loads qualitative cases from `benchmarks/qualitative_wikirace_cases.yaml`, computes summary metrics, and writes JSON, CSV, and Markdown reports.

## 4. Deployment Model

The repository is configured for Hugging Face Spaces using Docker. The Space starts Streamlit on port 8501:

```bash
streamlit run app.py --server.address=0.0.0.0 --server.port=8501 --server.headless=true
```

The public deployment should use:

| Setting | Value |
|---|---|
| SDK | Docker |
| Port | 8501 |
| `DEMO_MODE` | `true` |
| `ALLOW_LIVE_RUNS` | `false` |
| `DEFAULT_CONFIG_PATH` | `evals/config.yaml` |
| `REPORTS_DIR` | `reports` |
| `BENCHMARK_MODE` | `demo` |

This prevents public users from triggering live model calls or spending API quota.

## 5. Benchmark Design

The demo benchmark contains repository-grounded qualitative cases. It is deterministic and does not call external APIs. The cases cover:

| Case ID | Category | Status |
|---|---|---|
| `cycle-avoidance` | loop control | pass |
| `budget-awareness` | budget control | pass |
| `deterministic-fallback` | failure recovery | pass |
| `api-error-continuation` | external API handling | warning |
| `config-validation` | configuration safety | pass |
| `public-demo-safety` | deployment safety | pass |

Generated artifact paths:

- `reports/demo_benchmark/demo_results.json`
- `reports/demo_benchmark/demo_summary.csv`
- `reports/demo_benchmark/qualitative_case_gallery.md`

## 6. Qualitative Evaluation

The current demo report contains 6 cases, with 5 pass, 0 fail, and 1 warning. The computed pass rate is 83.33%. These values are generated from `benchmarks/qualitative_wikirace_cases.yaml` and are intended to demonstrate the evaluation interface, not live model performance.

The warning case documents that live API failure behavior still needs manual verification against a real WikiRace endpoint.

## 7. Error Handling and Reproducibility

The repository includes tests for:

- demo mode defaults disabling live execution
- missing `OPENAI_API_KEY` handling
- benchmark case loading
- deterministic demo benchmark generation
- summary metric computation
- report writing to a configured directory
- adapter URL encoding and timeout behavior
- config validation

Reproduction commands:

```bash
pip install -r requirements.txt
python -m src.generate_demo_benchmark --output reports/demo_benchmark
python -m pytest tests -q
streamlit run app.py --server.headless true --server.port 8501
```

## 8. Public Demo Mode and Safety Considerations

The dashboard defaults to public demo mode. In this mode:

- live model calls are disabled
- `OPENAI_API_KEY` is not required
- static reports are loaded from `reports/demo_benchmark`
- the sidebar shows whether a key is present without revealing it
- user-provided keys, if live mode is privately enabled, are session-only

This design allows a public CV or portfolio demo without exposing secrets or spending API quota.

## 9. Limitations

- The current repository is a WikiRace navigation evaluator, not a general LLM red-team suite.
- Demo results are deterministic and illustrative.
- Live evaluation requires `WIKIRACE_API_BASE_URL`.
- OpenAI-backed runs require `OPENAI_API_KEY` and explicit `--real-models`.
- Hugging Face free storage is ephemeral for runtime-generated files.
- Docker build/runtime verification requires a local Docker daemon.

## 10. Conclusion

The project now provides a public-safe dashboard, reproducible qualitative demo benchmark, CLI evaluation path, Docker/Hugging Face deployment support, and documentation that separates demo artifacts from live evaluation capability. This makes the repository suitable for portfolio demonstration while preserving a clear path to private, credentialed evaluation.

## 11. Reproducibility Checklist

| Item | Value |
|---|---|
| Python | 3.12 |
| Install | `pip install -r requirements.txt` |
| Tests | `python -m pytest tests -q` |
| Dashboard | `streamlit run app.py` |
| Demo benchmark | `python -m src.generate_demo_benchmark` |
| Docker build | `docker build -t llm-redteam-hf .` |
| HF SDK | Docker |
| HF port | 8501 |
| Safe public env | `DEMO_MODE=true`, `ALLOW_LIVE_RUNS=false` |
