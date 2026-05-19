# Probing LLM Layerwise Graph Embeddings for WikiRace Navigation

## One-line summary
Extract monosemantic article-relatedness features from intermediate LLM layers via SAE + AttnLRP, then use these latent graph embeddings to score next-step links without consuming the LLM's full token budget.

## Problem it solves
WikiRace treats LLMs as black boxes; their internal representations of Wikipedia knowledge are never examined. Token-budget inefficiency arises because models must evaluate all candidate links via generation. No interpretable signal for *why* the model chose a link exists.

## Method
1. Run LLM on WikiRace corpus, log activations from layers 15–30
2. Train routing SAE (~64 features, sparsity budget) on activations
3. Route A (SAE direct): embed source + candidate → relatedness logit via SAE + MLP (no LLM call)
4. Route B (LRP + SAE fusion): backpropagate link-selection decision via AttnLRP; weight SAE features by LRP relevance scores
5. Deploy hybrid: SAE+LRP pre-ranks links, LLM confirms only top-k=3–5
6. Estimated ~80% reduction in forward passes

## Key novelty
- Interpretable routing without token cost
- Layer attribution reveals which layers encode article relatedness
- Adaptive recovery by injecting heuristics in probed feature space
- Combines mech-interp tooling (SAE, LRP) with navigation task

## Feasibility notes
- SAE training: <24h on 1 GPU (~5–10M tokens)
- LRP: 2–4h (10k forward+backward passes)
- AttnLRP implementations exist (ICML 2024)
- Total timeline: ~2 weeks

## Risks / open questions
1. SAE may learn features orthogonal to graph structure
2. LRP backprop scaling to 7B+ LLMs
3. MLP mapping from LLM-internal semantics to link relevance may be noisy
4. Hard WikiRace instances may require multi-step planning beyond relatedness

## Axis: Interpretability / probing
