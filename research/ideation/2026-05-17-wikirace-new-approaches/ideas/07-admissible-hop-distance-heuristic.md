# Train a Hop-Distance Predictor for Admissible A* Navigation on Wikipedia

## One-line summary
Learn a lightweight Transformer (~100M params) mapping (source_article_text, target_title) → predicted_hops, calibrated to be admissible (never overestimate), enabling A* to replace greedy LLM navigation with a principled informed search.

## Problem it solves
No WikiRace system has a quantitative distance estimator — only qualitative "closer/farther" signals. Without an admissible heuristic, principled informed search (A*) is impossible. Perfect offline ground truth (Wikipedia's BFS distances) is freely available but unused.

## Method
1. BFS offline on Wikipedia link graph to compute shortest-path distances for sampled (source, target) pairs
2. Train small Transformer: source (512 tokens) + target (128 tokens) → predicted hops
3. Asymmetric loss: penalize overestimates 10× more than underestimates (enforces admissibility)
4. Clip predictions to [0, max_budget], round down
5. At each WikiRace step: f(next_link) = 1 + h(next_link, target) → A* with greedy tie-breaking

## Key novelty
- Admissibility by design via asymmetric loss (not post-hoc calibration)
- Unlimited ground truth from Wikipedia link graph
- Fast inference: <10ms, no LLM overhead
- Measurable regret: actual hops vs. predicted hops

## Feasibility notes
- Wikipedia link graph: ~5GB, publicly available
- Training: ~48h on H100
- Inference: CPU-bound, trivial
- Baseline: success rate, avg hops, nodes expanded vs. greedy LLM

## Risks / open questions
1. Graph distribution shift: training pairs ≠ WikiRace game pairs
2. Long-tail collapse on >15-hop pairs (rare in training)
3. Floating-point admissibility slip near boundaries
4. A* branching factor on Wikipedia may require strong pruning

## Axis: Learned distance heuristics
