# Phase 2 ablations

Phase 2 makes the experimental comparison valid by ensuring that the same agent loop is used across modes and that differences arise from configuration-controlled capabilities.

## What Phase 2 implements
- centralized `ModeConfig` presets
- one loop controlled by capability flags
- shared instance set/order across all modes
- per-mode result files and combined summary

## Modes
- **baseline**: chat-style direct move selection, no invariant shell interventions
- **state_only**: strict state + acyclicity/budget gate only
- **stratified**: tactical+strategic with periodic replan only
- **full**: all Phase 1 controls enabled

## Commands
Smoke:
`python scripts/run_phase2_ablations.py --difficulty easy --limit 3 --modes baseline,state_only,stratified,full --config configs/stratified_navigator.yaml --output-dir outputs/phase2_mock_smoke --mock`

100 hard:
`python scripts/run_phase2_ablations.py --difficulty hard --limit 100 --modes baseline,state_only,stratified,full --config configs/stratified_navigator.yaml --output-dir outputs/phase2_ablations`

All difficulties:
`python scripts/run_phase2_ablations.py --difficulty all --limit-per-difficulty 100 --modes baseline,state_only,stratified,full --config configs/stratified_navigator.yaml --output-dir outputs/phase2_ablations`

## Not included yet
- Phase 3 cost telemetry
- publication-ready reporting/leaderboards

Do not claim benchmark improvements unless live runs completed.
