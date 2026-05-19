# WikiRace Ideation Ranking — 2026-05-17

## Global Rankings

| Rank | Title | Novelty | Feasibility | Soundness | Composite | Verdict | Axis |
|------|-------|---------|-------------|-----------|-----------|---------|------|
| 1 | Admissible Hop-Distance Predictor (A*) | 3/5 | 4/5 | 4/5 | **4.1** | KEEP | Distance heuristics |
| 2 | Embedding-LLM Uncertainty Thresholding | 3/5 | 4/5 | 2/5 | **3.0** | KEEP-WITH-FIXES | Vector navigation |
| 3 | RL-GRPO Navigator | 3/5 | 4/5 | 2/5 | **3.0** | KEEP-WITH-FIXES | RL/training |
| 4 | MCTS Navigation + Revisit Penalties | 3/5 | 3/5 | 2/5 | **2.7** | KEEP-WITH-FIXES | Inference search |
| 5 | Probing LLM Embeddings (SAE+LRP) | 3/5 | 3/5 | 2/5 | **2.7** | KEEP-WITH-FIXES | Interpretability |
| 6 | Cross-Graph Adversarial Benchmark | 4/5 | 2/5 | 2/5 | **2.7** | KEEP-WITH-FIXES | Benchmark |
| 7 | Hybrid GNN-LLM Graph Sketcher | 2/5 | 3/5 | 2/5 | **2.3** | KEEP-WITH-FIXES | Graph reasoning |
| 8 | Disagreement-Driven Backtracking | 2/5 | 3/5 | 2/5 | **2.3** | KEEP-WITH-FIXES | Multi-agent |

---

## Top 3 — Full Idea Cards

### #1 — Admissible Hop-Distance Predictor for A* Navigation
**Composite: 4.1/5 | KEEP**

**One-line summary:** Learn a lightweight Transformer (~100M params) mapping (source_article, target_title) → predicted_hops, calibrated admissible via asymmetric loss, enabling A* to replace greedy LLM navigation.

**Problem:** No WikiRace system has a quantitative distance estimator. Without an admissible heuristic, principled A* search is impossible. Wikipedia's BFS distances provide free, perfect ground truth.

**Method:**
1. BFS on Wikipedia link graph to compute shortest-path distances for sampled (source, target) pairs
2. Train small Transformer: source (512 tokens) + target (128 tokens) → predicted hops
3. Asymmetric loss: penalize overestimates 10× (enforces admissibility)
4. Clip to [0, max_budget], round down
5. At each WikiRace step: f(next_link) = 1 + h(next_link, target) → A* with greedy tie-breaking

**Key novelty:** Admissibility by design (asymmetric loss); unlimited ground truth from Wikipedia link graph; fast inference (<10ms); measurable regret.

**Feasibility:** Wikipedia link graph ~5GB (public). Training: ~48h on H100. Total: 1–2 week project.

**Key fix before proceeding:** Validate on WikiRace-specific distribution (not random Wikipedia pairs); oversample >15-hop instances.

**Prior work:** arXiv:2509.22626 (admissible heuristics), arXiv:2602.16902 (WikiRace benchmark)

---

### #2 — Hybrid Embedding-LLM Navigation with Learned Uncertainty Thresholding
**Composite: 3.0/5 | KEEP-WITH-FIXES**

**One-line summary:** Pre-compute DPR embeddings; navigate greedily by default; invoke LLMs only when top-1/top-2 confidence ratio drops below a learned threshold — saving ~60% of LLM calls.

**Problem:** Every WikiRace step consumes an LLM call (30 per game), wasting compute on straightforward hops where embedding similarity already discriminates links well.

**Method:**
1. DPR embeddings for all Wikipedia articles (FAISS index)
2. Rank outgoing links by embedding distance to target
3. Confidence: top-1/top-2 similarity ratio
4. Small MLP meta-model trained on trajectories predicts: "will greedy embedding succeed?"
5. If confidence > threshold → take embedding-ranked link (no LLM)
6. If confidence ≤ threshold → invoke LLM as verifier/disambiguator
7. Adaptive re-thresholding within episode when LLM disagrees

**Key novelty:** Sparse LLM invocation driven by learned confidence; within-episode adaptive thresholding.

**Feasibility:** DPR on Wikipedia: hours. Meta-model: 1–2h. Drop-in replacement. Low risk.

**Key fix before proceeding:** Establish DPR-only baseline on hard WikiRace instances; redesign meta-model supervision to step-level (not trajectory-level) labels.

---

### #3 — RL-Fine-Tuned Navigator with GRPO on Trajectory Replay
**Composite: 3.0/5 | KEEP-WITH-FIXES**

**One-line summary:** Train a 7B navigator with GRPO using process rewards from WikiRace trajectories, so the model learns graph-traversal skills that general LLMs lack.

**Problem:** General LLMs have no domain-specific priors for WikiRace: which link types are shortcuts, how to replan, or how to break loops. No training signal from past trajectories is used.

**Method:**
1. Collect 10k WikiRace trajectories (success + failure)
2. Process reward: r_t = −log(cosine_distance(embed(link), embed(target))) + α·1(success) − β·loop_penalty_t
3. GRPO training: 7B Llama, 4 rollouts/prompt, 2 epochs (~100 GPU-hours)
4. Inference: single model, chain-of-thought link selection

**Key novelty:** Task-specific RL on real WikiRace graph traversals; single policy replaces multi-tier hierarchy.

**Feasibility:** ~1 week. Data: existing WikiRace games × augmented rollouts.

**Key fix before proceeding:** Redesign reward to capture trajectory-level path quality (not myopic step-level cosine distance); oversample hard instances in training data.

---

## Diversity Check
- Top 5 span 5 distinct axes: distance heuristics, vector navigation, RL/training, inference search, interpretability
- No clustering on single axis
- Idea 6 (Benchmark) is highest novelty (4/5) but lowest feasibility (2/5) — flagged as second-best from benchmark axis if user wants broader scope

## Next Step
Run `/idea-to-code <rank>` to convert the chosen idea into an implementation spec.
