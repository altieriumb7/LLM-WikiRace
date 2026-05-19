# RL-Fine-Tuned Navigator with Link-Valuation Rewards from Trajectory Replay

## One-line summary
Train a 7B specialized navigator end-to-end with GRPO on WikiRace trajectories, using process rewards (link-to-target semantic distance) from successful/failed paths, replacing multi-tier LLM hierarchy with a single aligned policy.

## Problem it solves
General-purpose LLMs lack domain-specific priors about: which link types are shortcuts vs. dead ends; how to replan after failure; semantic momentum of traversals. No training signal from past WikiRace trajectories is used in any current approach.

## Method
1. Collect 10k WikiRace trajectories (success + failure)
2. Process reward: r_t = −log(cosine_distance(embed(link), embed(target))) + α·1(success) − β·loop_penalty_t
3. GRPO training: 7B Llama backbone, 4 rollouts per prompt, normalize advantages, 2 epochs
4. Inference: single model, chain-of-thought link selection

## Key novelty
- Task-specific RL signal from real graph traversals
- Step-level process rewards exploit semantic geometry
- Single aligned policy replaces multi-tier hierarchy
- No GRPO-trained WikiRace navigator exists in literature

## Feasibility notes
- Data: 1000+ existing games × 30 steps, augmentable to 10k
- Compute: ~100 GPU-hours (RTX 4090)
- Timeline: ~1 week
- Compare against GPT-4o, Claude-3.5-Sonnet zero-shot

## Risks / open questions
1. Reward heuristic is myopic (local semantic ≠ global path quality)
2. Domain shift on hard instances
3. Loop penalties may suppress valid hub revisits
4. Framing vs. larger frontier models requires honest experimental design

## Axis: RL / training-time
