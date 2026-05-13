---
title: LLM Red Team Evaluation Dashboard
emoji: 🧪
colorFrom: red
colorTo: gray
sdk: docker
app_port: 8501
pinned: false
---

# LLM WikiRace Evaluation Dashboard

This repository contains a Python/Streamlit dashboard and CLI tools for evaluating LLM-guided WikiRace navigation strategies. The current codebase is a WikiRace evaluator, not a generic red-team harness: the public demo highlights qualitative navigation safety and reliability cases such as loop avoidance, budget control, fallback behavior, config validation, and API error reporting.

## Live Demo on Hugging Face Spaces

The Space is designed to run safely in public demo mode. Public visitors can inspect static benchmark artifacts without triggering live provider calls or spending API quota.

Safe demo defaults:

- `DEMO_MODE=true`
- `ALLOW_LIVE_RUNS=false`
- `BENCHMARK_MODE=demo`
- No `OPENAI_API_KEY` required

The dashboard visibly reports whether an API key is present, but never displays the key.

## Local Setup

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r requirements.txt
streamlit run app.py
```

## CLI Evaluation

Mock/local run:

```powershell
python scripts/run_phase2_ablations.py --mock --difficulty easy --limit 10 --output-dir outputs/phase2_ablations
```

Live deterministic WikiRace API run:

```powershell
$env:WIKIRACE_API_BASE_URL="https://your-api.example"
python scripts/run_phase2_ablations.py --difficulty hard --limit 100 --output-dir outputs/phase2_ablations
```

Live OpenAI-backed run:

```powershell
$env:WIKIRACE_API_BASE_URL="https://your-api.example"
$env:OPENAI_API_KEY="..."
python scripts/run_phase2_ablations.py --real-models --difficulty hard --limit 100 --output-dir reports/live_run
```

Official benchmark evaluation requires the optional external benchmark package:

```powershell
python -m pip install -e ".[benchmark]"
python scripts/run_benchmark_batch_eval.py --mode-config configs/modes/full.yaml --difficulty hard --batch-size 16
```

## Demo Benchmark

The public demo benchmark is deterministic and does not call external APIs.

Generate it with:

```powershell
python -m src.generate_demo_benchmark --output reports/demo_benchmark
```

Artifacts:

- `reports/demo_benchmark/demo_results.json`
- `reports/demo_benchmark/demo_summary.csv`
- `reports/demo_benchmark/qualitative_case_gallery.md`

Metrics shown in the dashboard:

- total cases
- pass/warning/fail counts
- pass rate
- categories covered
- qualitative case gallery

Current demo artifacts contain 6 cases: 5 pass and 1 warning. These are illustrative repository-grounded checks, not claims of live model performance.

## Docker

```bash
docker build -t llm-redteam .
docker run --rm -p 8501:8501 --env-file .env llm-redteam
```

For a safe public-style run without `.env`:

```bash
docker run --rm -p 8501:8501 -e DEMO_MODE=true -e ALLOW_LIVE_RUNS=false llm-redteam
```

## Hugging Face Spaces Deployment

1. Create a new Hugging Face Space.
2. Select SDK: Docker.
3. Push this repository.
4. Set Variables:
   - `DEMO_MODE=true`
   - `ALLOW_LIVE_RUNS=false`
   - `DEFAULT_CONFIG_PATH=evals/config.yaml`
   - `REPORTS_DIR=reports`
   - `BENCHMARK_MODE=demo`
5. Optional Secret:
   - `OPENAI_API_KEY`

Hugging Face free storage is ephemeral. Demo artifacts are committed under `reports/demo_benchmark`; runtime live reports should be treated as temporary unless exported.

## Security

- No real `.env` or API keys should be committed.
- Public demo mode disables live execution by default.
- User-provided dashboard keys are session-only and are not persisted.
- Any live OpenAI-backed CLI run requires explicit `--real-models`.

## Verification

```powershell
python -m compileall -q src scripts tests app.py
python -m pytest tests -q
python -m src.generate_demo_benchmark
streamlit run app.py --server.headless true --server.port 8501
```

## Limitations

- This repository is a WikiRace navigation evaluator, not a general red-team benchmark suite.
- Demo benchmark results are illustrative and deterministic.
- Live evaluation requires API credentials and a reachable WikiRace API.
- Docker runtime verification requires a running Docker daemon.

## Portfolio Summary

This project demonstrates a deployable evaluation dashboard with safe public defaults, reproducible demo artifacts, tested config/benchmark helpers, and a documented path from static portfolio demo to private live evaluation.
