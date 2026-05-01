# Core loop refactor

The ablation study is interpretable only if every mode uses the same navigation loop and all behavioral differences come from injected strategy objects.

This refactor deletes legacy competing paths, keeps one loop in `agent.py`, and centralizes mode behavior in `build_strategy`.

Baseline is intentionally weak and unconstrained to avoid structured assistance contamination.

Run dry-run validation:

`python scripts/run_phase2_ablations.py --dry-run`

Run tests:

`python -m pytest tests/`

Before live benchmark collection, real model clients and production API bindings still need to be wired in this minimal topology.
