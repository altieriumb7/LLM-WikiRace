# Critique Batch 1 — Ideas 1–4

## Idea 1: Hybrid GNN-LLM Graph Sketcher
- Novelty: 2/5 — Commute-time + GNN clustering is established; WikiRace application is incremental
- Feasibility: 3/5 — Engineering is sound but A* integration is underspecified
- Soundness: 2/5 — Core hypothesis (structural distance predicts semantic path quality) unvalidated; may contradict arXiv:2511.10585
- Composite: 2.3/5
- Verdict: KEEP-WITH-FIXES
- Key fix: Validate commute-time correlation with path quality before building GNN sketch

## Idea 2: MCTS Navigation + Revisit Penalties
- Novelty: 3/5 — MCTS+LLM exists; revisit penalty for WikiRace loops is a reasonable application
- Feasibility: 3/5 — Feasible but hyperparameter tuning (UCB, penalty, budget) is underestimated
- Soundness: 2/5 — No justification that MCTS beats greedy on WikiRace; greedy semantic ranking may already be near-optimal
- Composite: 2.7/5
- Verdict: KEEP-WITH-FIXES
- Key fix: Run oracle greedy vs. MCTS ablation on 50 hard instances before committing

## Idea 3: Embedding-LLM Uncertainty Thresholding
- Novelty: 3/5 — Confidence-driven oracle invocation is a known pattern; DPR upgrade is incremental
- Feasibility: 4/5 — DPR + meta-model is a drop-in, 1–2 week project
- Soundness: 2/5 — Supervision signal (trajectory-level) doesn't map to step-level confidence; baseline unclear
- Composite: 3.0/5
- Verdict: KEEP-WITH-FIXES
- Key fix: Validate DPR-only baseline on hard instances; design step-level supervision signal for meta-model

## Idea 4: RL-GRPO Navigator
- Novelty: 3/5 — GRPO on task trajectories is established; WikiRace-specific fine-tuning is new
- Feasibility: 4/5 — ~100 GPU-hours, 1 week; data collection is the bottleneck
- Soundness: 2/5 — Step-level reward (cosine distance) is myopic; will likely replicate greedy embedding ranking
- Composite: 3.0/5
- Verdict: KEEP-WITH-FIXES
- Key fix: Redesign reward to capture trajectory-level path quality, not just step-level proximity
