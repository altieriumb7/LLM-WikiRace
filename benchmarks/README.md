# Qualitative Demo Benchmark

This benchmark is a deterministic public-demo layer for the WikiRace navigation evaluator.

It does not call external APIs and does not claim live model performance. The cases are small qualitative checks based on repository behavior: config validation, loop control, budget control, fallback behavior, API error reporting, and safe public deployment defaults.

Generate artifacts:

```bash
python -m src.generate_demo_benchmark --output reports/demo_benchmark
```

Generated files:

- `reports/demo_benchmark/demo_results.json`
- `reports/demo_benchmark/demo_summary.csv`
- `reports/demo_benchmark/qualitative_case_gallery.md`
