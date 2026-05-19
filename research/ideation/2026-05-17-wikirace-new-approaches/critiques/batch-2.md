# Critique Batch 2 — Ideas 5–8

## Idea 5: Disagreement-Driven Recursive Backtracking
- Novelty: 2/5 — Multi-agent debate, entropy detection, and rollback all exist separately; combination is incremental
- Feasibility: 3/5 — No fine-tuning needed; rollback state management adds engineering complexity (~3–4 weeks)
- Soundness: 2/5 — Core assumption unvalidated: no evidence LLM disagreement predicts dead-ends in WikiRace
- Composite: 2.3/5
- Verdict: KEEP-WITH-FIXES
- Key fix: Validate that high-entropy steps empirically predict failure on WikiRace before building the system

## Idea 6: Probing LLM Layerwise Embeddings (SAE+LRP)
- Novelty: 3/5 — SAE routing + AttnLRP fusion is new combination; individual components well-established
- Feasibility: 3/5 — SAE training feasible; LRP backprop at 7B+ scale is expensive and uncertain
- Soundness: 2/5 — SAE features optimized for reconstruction, not graph structure; may be orthogonal to article relatedness
- Composite: 2.7/5
- Verdict: KEEP-WITH-FIXES
- Key fix: Validate SAE feature alignment with article relatedness (inspect top features; >50% should be human-interpretable as relatedness)

## Idea 7: Admissible Hop-Distance Predictor (A*)
- Novelty: 3/5 — Learning admissible heuristics is known; Wikipedia hop-distance application is new
- Feasibility: 4/5 — Public data, ~48h training, trivial inference; clean 1–2 week project
- Soundness: 4/5 — Asymmetric loss for admissibility is well-motivated; ground truth is abundant and objective; metrics are clear
- Composite: 4.1/5
- Verdict: KEEP
- Key fix: Validate on WikiRace-specific distribution (not random Wikipedia pairs)

## Idea 8: Cross-Graph Adversarial Benchmark
- Novelty: 4/5 — No prior benchmark combines Wikidata + multilingual + temporal for navigation evaluation
- Feasibility: 2/5 — Wikidata sparsity, multilingual quality variance, and historical snapshot reconstruction are serious data engineering challenges (~6–8 weeks)
- Soundness: 2/5 — Multiple confounders (sparsity, coverage, temporal asymmetry) make results hard to interpret without careful controls
- Composite: 2.7/5
- Verdict: KEEP-WITH-FIXES
- Key fix: Pre-filter infeasible pairs (path length ≤30 across all variants); stratify by path-length bucket; start with multilingual leg only
