# Disagreement-Driven Recursive Backtracking via Speculative Debate

## One-line summary
Deploy K heterogeneous LLM agents to propose next links in parallel; use strong disagreement as a signal to trigger automatic rollback to the last consensus point, rather than naively executing majority-vote links that hide divergence.

## Problem it solves
Single-agent and naive ensemble WikiRace systems fail because: (1) silent agreement hides uncertainty — all agents agreeing on a trap gives no signal; (2) majority voting suppresses minority dissent; (3) no recovery mechanism — replanning starts from a poisoned state.

## Method
1. Maintain "consensus frontier": last point where all K agents agreed
2. At each step, K agents (different sizes/architectures) propose top-3 links
3. Compute disagreement entropy (Gini coefficient)
4. If entropy > threshold T: run arbitration round — prompt each agent with debate history, collect justifications, feed to meta-reasoner
5. Meta-reasoner decides: execute majority, execute dissent, or rollback to consensus frontier
6. On rollback: restore state (zero step cost), agents re-plan next 3–5 steps with debate history as context

## Key novelty
- Disagreement as epistemic risk signal (not noise)
- Speculative debate without consuming steps
- Rollback with poisoned-path awareness
- Heterogeneous agents amplify meaningful divergence

## Feasibility notes
- No fine-tuning required
- K parallel API queries per step
- Rollback budget caps infinite loops (e.g., max 2 per game)
- Hardware: 1 GPU + multiple API accounts

## Risks / open questions
1. Small models may disagree randomly, not for principled reasons
2. Rollback infinite loops without budget cap
3. Meta-reasoner (Opus) latency and cost per dispute
4. Ensemble diversity requires careful agent selection

## Axis: Multi-agent debate
