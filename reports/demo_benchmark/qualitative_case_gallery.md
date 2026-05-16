# Demo Qualitative Benchmark Gallery

These are deterministic sample results for the public demo. They do not claim live model performance.

- Total cases: 6
- Pass: 5
- Warning: 1
- Fail: 0
- Pass rate: 83%
- Non-failing rate: 100%

## cycle-avoidance: loop control

- Status: pass
- Input: Current page A has links back to A and forward to D while target is T.
- Expected: Prefer an unvisited forward candidate and avoid repeating pages.
- Observed demo output: The deterministic controller skips visited pages when non-visited candidates exist.
- Assessment: Shows the value of explicit visited-state tracking for WikiRace navigation.
- Notes: Grounded in StatefulStrategy loop checks and fallback tests.

## budget-awareness: budget control

- Status: pass
- Input: A candidate appears promising but its estimated distance exceeds remaining steps.
- Expected: Reject candidates that cannot fit within the step budget.
- Observed demo output: Budget checks prevent selecting candidates where steps_used + 1 + estimated_dist exceeds budget.
- Assessment: Demonstrates transparent constraint handling instead of purely greedy link choice.
- Notes: Grounded in budget pruning tests.

## deterministic-fallback: failure recovery

- Status: pass
- Input: The ranker returns only rejected candidates but an unvisited outgoing link remains.
- Expected: Use deterministic fallback rather than crashing or silently stopping.
- Observed demo output: Fallback selects an unvisited page and records fallback usage.
- Assessment: Improves demo robustness and produces auditable counters.
- Notes: Grounded in fallback module and runner counters.

## api-error-continuation: external API handling

- Status: warning
- Input: The live WikiRace API raises an HTTP or malformed response error.
- Expected: Return a failed result with an API error counter instead of masking the failure.
- Observed demo output: The game loop catches adapter errors and returns failure_reason=api_error.
- Assessment: Good for batch evaluation because failures become reportable data.
- Notes: Live API behavior still requires manual verification with a real endpoint.

## config-validation: configuration safety

- Status: pass
- Input: A baseline mode config enables full-strategy-only settings.
- Expected: Reject invalid config before a run starts.
- Observed demo output: ModeConfig raises ConfigValidationError for invalid combinations.
- Assessment: Protects reproducibility by failing early on incompatible modes.
- Notes: Grounded in config validation tests.

## public-demo-safety: deployment safety

- Status: pass
- Input: A public visitor opens the Hugging Face Space without credentials.
- Expected: Show static demo artifacts and disable live model/API spending.
- Observed demo output: Dashboard defaults to DEMO_MODE=true and ALLOW_LIVE_RUNS=false.
- Assessment: Suitable for portfolio hosting without exposing or spending API quota.
- Notes: Implemented in app settings and dashboard guardrails.
