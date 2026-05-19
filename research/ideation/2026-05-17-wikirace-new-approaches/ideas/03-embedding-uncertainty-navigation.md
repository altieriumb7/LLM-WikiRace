# Hybrid Embedding-LLM Navigation with Learned Uncertainty Thresholding

## One-line summary
Pre-compute article embeddings using contrastive models (DPR), navigate greedily via embedding similarity, and invoke LLMs only when embedding-space confidence drops below a learned threshold, avoiding ~70% of LLM calls.

## Problem it solves
LLM-WikiRace invokes an LLM at every step (30 calls per game), wasting compute on straightforward hops that embedding-space similarity handles well. Current system treats trivial and ambiguous hops identically.

## Method
**Offline:** Compute DPR embeddings for all Wikipedia articles. Store in FAISS.

**Online navigation:**
1. Rank outgoing links by embedding distance to target
2. Compute confidence: top-1/top-2 similarity ratio
3. Small meta-model (MLP, trained on 500–1000 trajectories) predicts: "will greedy embedding succeed?"
4. If confidence > threshold → take embedding-ranked link (zero LLM cost)
5. If confidence ≤ threshold → invoke LLM as verifier/disambiguator
6. Adaptive re-thresholding if LLM disagrees with embedding top-1

## Key novelty
- Confidence-driven sparse LLM invocation
- Learned threshold adapts within episode
- Semantic context aggregation of outgoing links
- Directly targets token-budget bottleneck

## Feasibility notes
- DPR embedding on Wikipedia: hours on 1 GPU
- Meta-model training: 1–2h
- Estimated 60% token savings
- Drop-in replacement for link ranking module

## Risks / open questions
1. Embedding collapse on ambiguous pages (e.g., "John Smith")
2. Multimodal DPR may not add value over text-only
3. Meta-model generalization to hard instances
4. Supervision signal for contrastive learning unclear

## Axis: Semantic vector navigation
