# WikiRace Research Ideation — 2026-05-17

## Topic
Improve LLM-guided Wikipedia link navigation (WikiRace) beyond the current multi-tiered tactical/strategic LLM hierarchy, replacing or augmenting it with methods that achieve shorter paths, fewer API calls, and better trap escape.

## Current approach
Multi-tiered hierarchical navigation (Baseline, Stateful, Stratified, Full strategies) with PageRank fallback, decay-based replanning, and trap detection. Core bottleneck: LLMs see only local link lists with no global graph structure.

## Diversity axes
1. Graph-structured reasoning — GNN/graph embeddings for global structural awareness
2. Inference-time search — MCTS or A* guided by LLM heuristics
3. Semantic vector navigation — Pre-compute embeddings, invoke LLM only for disambiguation
4. RL / training-time — Fine-tune or GRPO-train on WikiRace trajectories
5. Multi-agent debate — Ensemble voting with debate/rollback protocol
6. Interpretability / probing — Extract implicit graph knowledge from LLM internals
7. Learned distance heuristics — Train admissible hop-distance estimator for A*
8. Benchmark extension — Wikidata, multilingual, temporal graph variants

## N generators: 8 (Haiku)
## N critic batches: 2 (Sonnet)
