# MCTS-Guided Wikipedia Navigation with LLM Link Ranking and Revisit Penalties

## One-line summary
Use Monte Carlo Tree Search with the LLM as a link-ranking heuristic and Wikipedia link graph structure as the world model, adding explicit revisit penalties to break loops and enable deep lookahead where greedy navigation fails.

## Problem it solves
Current LLM-WikiRace systems fail on: (1) no lookahead — greedy link selection commits to bad branches early; (2) loop entrapment — repeated visits with no structural recovery mechanism.

## Method
Replace greedy link-selection with MCTS:
- State: current Wikipedia article
- Actions: available hyperlinks
- Policy (LLM): rank links via embedding distance, return normalized scores
- World model: deterministic Wikipedia graph
- Revisit penalty: subtract constant from reward for nodes visited in same rollout
- 50–200 simulations per step (2–3 sec budget)
- Select link by highest visit count
- LLM is heuristic, not decision-maker

## Key novelty
- LLM as heuristic not agent (decoupled roles)
- Explicit loop detection via rollout penalties targets observed WikiRace failure mode
- Fixed deterministic world model (simpler than LLM-generated world models)
- No fine-tuning required; wraps any existing LLM

## Feasibility notes
- Embedding-based ranking reduces LLM calls to ~1 per step
- 4–6 hours to first result
- Hardware: API access + Wikipedia link cache
- Test on 100 hard-instance pairs

## Risks / open questions
1. MCTS overhead may not improve over greedy if heuristic is already strong
2. Embedding quality is the bottleneck
3. Revisit penalty hyperparameter sensitivity
4. Depth bias in tree expansion
5. Empirical: does lookahead actually help on WikiRace?

## Axis: Inference-time search
