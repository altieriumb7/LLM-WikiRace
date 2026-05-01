# Phase 1 live runner

Phase 1 validates the control-shell invariants and live adapter behavior. It is not yet the full ablation study.

## Implements
- strict state contract and validated transitions
- deterministic invariant gate + fallback order
- replan/escape trigger semantics
- live adapter with retries/backoff
- resumable checkpointed runner

## Does not implement
- full ablation refactor
- leaderboard reporting
- full cost accounting

## Required env vars
- `OPENAI_API_KEY`
- `WIKIRACE_API_BASE_URL`

## Commands
Smoke (5):
`python scripts/run_live_phase1.py --difficulty easy --limit 5 --config configs/stratified_navigator.yaml --output-dir outputs/live_phase1_smoke`

Live (100):
`python scripts/run_live_phase1.py --difficulty hard --limit 100 --config configs/stratified_navigator.yaml --output-dir outputs/live_phase1`

Resume:
`python scripts/run_live_phase1.py --resume outputs/live_phase1/<run_id>/checkpoint.json --config configs/stratified_navigator.yaml`

Warning: no benchmark result is claimed unless the live command has completed.
