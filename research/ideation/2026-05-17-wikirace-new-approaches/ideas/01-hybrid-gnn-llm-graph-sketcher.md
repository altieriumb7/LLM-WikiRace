# Hybrid GNN-LLM Graph Sketcher for WikiRace Lookahead — Expanded

## One-line summary
Pre-compute a hierarchical GNN sketch of Wikipedia's link graph offline; at inference, inject cluster-level structural priors into the LLM's link-ranking to give it global topology awareness without real-time graph queries.

---

## Problem statement (sharpened)

The current best WikiRace navigators achieve ~23% on hard instances. The failure mode is well-diagnosed in arXiv:2602.16902: navigators loop, make locally plausible but globally catastrophic link choices, and cannot recover because replanning starts from a poisoned state with no structural oracle.

Root cause: **LLMs only see the local link list of the current article**. They cannot distinguish "this link looks good semantically but leads to a structurally isolated cluster" from "this link is the actual bridge to the target's neighborhood."

The critic flagged that commute-time structural distance may not align with semantic navigability. The expanded design addresses this by making structural signals **one input among several** rather than the sole driver, and by validating the correlation empirically before deployment.

---

## Background: why commute-time?

The **commute-time distance** $C(u, v)$ between nodes $u$ and $v$ is the expected number of steps for a random walk to travel from $u$ to $v$ and back:

$$C(u, v) = \text{vol}(G) \cdot \|L^+e_u - L^+e_v\|^2$$

where $L^+$ is the Moore–Penrose pseudoinverse of the Laplacian, $e_u$ is the indicator vector for node $u$, and $\text{vol}(G) = \sum_i d_i$.

Key properties relevant to WikiRace:
- **Content-invariant**: purely structural, not semantic.
- **Captures bottlenecks**: high commute-time = few, narrow paths between nodes.
- **Detects hubs**: hub articles (e.g., "United States", "Mathematics") have low commute-time to most articles in their domain.
- **Tractable at cluster level**: exact computation on 15M nodes is infeasible; approximating on 5K super-nodes reduces it to a tractable $O(5000^2)$ matrix inversion.

---

## Method (detailed)

### Phase 1 — Offline graph construction

**Step 1.1 — Wikipedia link graph extraction**
- Download Wikimedia SQL dump (`enwiki-latest-pagelinks.sql.gz`, ~8GB compressed).
- Extract directed edges: `(source_article_id, target_article_id)`, main namespace only (ns=0).
- Filter: retain articles with ≥5 outgoing and ≥5 incoming links (removes disambiguation pages and orphan stubs).
- Result: ~12M nodes, ~120M directed edges.

**Step 1.2 — GraphSAGE training**
- Node features: title + first paragraph (128 tokens) encoded by frozen `all-MiniLM-L6-v2` (384-dim).
- Model: **GraphSAGE** (Hamilton et al., arXiv:1706.02216), 3 layers, mean aggregator, 64-dim hidden, 32-dim output.
- Self-supervised objective: link prediction (positive = existing edge; negative = random non-edge, ratio 1:5).
- Training: batch 512 nodes + 10-hop neighborhood sampling, ~48h on 1× RTX 4090 using PyG `NeighborSampler`.
- Output: 32-dim structural embedding per article capturing neighborhood topology.

**Step 1.3 — Hierarchical clustering**
- k-means on GraphSAGE embeddings, $k=5000$ clusters (~2400 articles per super-node).
- Per cluster: store (a) top-20 highest-PageRank articles as "representatives", (b) a 5-word label generated offline: `"Articles: [top-5 titles]. Summarize in 5 words."` → cache ~5K labels.

**Step 1.4 — Commute-time approximation at cluster level**
- Build super-node adjacency matrix $\hat{A} \in \mathbb{R}^{5000 \times 5000}$: $\hat{A}_{ij}$ = edge count between cluster $i$ and $j$, normalized by cluster sizes. Symmetrize.
- Compute cluster-level Laplacian $\hat{L}$; compute pseudoinverse $\hat{L}^+$ via truncated SVD (top 500 singular values).
- Pre-compute commute-time table $\hat{C}_{ij}$ for all cluster pairs — stored as 200MB float32 matrix (compressed ~50MB with LZ4).
- **Total offline cost**: ~3 days compute, ~60MB disk.

**Step 1.5 — Validation gate (mandatory before deployment)**

On a held-out set of 500 WikiRace source→target pairs:
1. Compute cluster-level commute-time: $\hat{C}(\text{cluster}(s), \text{cluster}(t))$.
2. Compute BFS shortest-path length $d^*(s, t)$.
3. Compute Spearman $\rho(\hat{C}, d^*)$.
4. **Decision**: if $\rho < 0.3$ → discard structural prior, fallback to pure semantic navigation. If $\rho \geq 0.3$ → proceed with integration.

~70% confident $\rho \geq 0.3$: Wikipedia's hub topology is well-documented and commute-time correlates with effective graph distance in scale-free networks.

---

### Phase 2 — Navigation with structural priors

**Augmented prompt:**
```
Current: [article] (cluster: "[cluster_label_current]").
Target: [target] (cluster: "[cluster_label_target]").

Structural context:
- You are in cluster "[cluster_label_current]" (e.g., "European geography and history").
- The target is in cluster "[cluster_label_target]" (e.g., "Nobel Prize laureates in Physics").
- Structural distance to target cluster: [NEAR / MEDIUM / FAR]
  (commute-time percentile: <33% = NEAR, 33–66% = MEDIUM, >66% = FAR)

Candidate links with structural signals:
- [link_1] → cluster "[cluster_label_1]", structural distance: NEAR ↓ (closer to target)
- [link_2] → cluster "[cluster_label_2]", structural distance: FAR ↑ (farther from target)
- [link_3] → cluster "[cluster_label_3]", structural distance: NEAR ↓
...

Rank these links by how likely each is to lead to [target] in the fewest steps.
```

**Combined scoring function:**

Let $s_i^{\text{LLM}} = 1 / r_i^{\text{LLM}}$ (inverse rank from LLM output). Structural affinity:

$$\text{affinity}_i = \exp\!\left(-\beta \cdot \frac{\hat{C}(\text{cluster}(i),\, \text{cluster}(t))}{\hat{C}_{\text{median}}}\right)$$

Final score:

$$s_i^{\text{combined}} = s_i^{\text{LLM}} \cdot (1 + \alpha \cdot \text{affinity}_i)$$

Select link with highest $s_i^{\text{combined}}$. Setting $\alpha = 0$ recovers the baseline LLM navigator exactly.

Hyperparameter grid: $\alpha \in \{0.2, 0.5, 1.0, 2.0\}$, $\beta \in \{0.5, 1.0, 2.0\}$ — tune on 200 validation pairs.

---

### Phase 3 — Strategic replanning with cluster waypoints

When replanning triggers (decay-based or trap detection), inject a cluster-level path into the strategic prompt:

```
Current: [article] (cluster: "[label]").
Target: [target] (cluster: "[target_label]").
Structural path to target: [label_1] → [label_2] → [label_3] → [target_label]
  (shortest path through super-nodes; each hop ≈ 2400 articles)

Your next milestone: reach an article in cluster "[label_2]".
Plan your next 3 steps with this milestone in mind.
```

The cluster-level path is computed on-the-fly with Dijkstra on the 5K×5K cluster graph (sub-millisecond). This gives the strategic LLM a concrete intermediate goal rather than a vague "get closer to target."

---

## Addressing the critic's concerns

**Commute-time vs. semantic distance:** The validation gate (Step 1.5) makes this empirical. If the signal is absent ($\rho < 0.3$), the prior is discarded. The combined score keeps LLM semantic judgment as the base; structural affinity is a multiplicative bonus, never the sole driver.

**Wikipedia link artifacts:** Cluster-level aggregation smooths per-article noise. Overly-dense articles contribute proportionally to their cluster's edge count (normalized by cluster size). Niche articles land in isolated clusters with high commute-time to everywhere else — which correctly signals "avoid unless target is here."

**Underspecified A\*:** A\* runs at the **cluster level** (branching factor ~20–50), not the article level (branching factor ~50–200). The cluster path provides waypoints; the LLM handles micro-navigation within clusters. This is the Feudal / hierarchical planning pattern (Nachum et al., arXiv:1805.08296) adapted to prompt-based navigation.

---

## Experiment design

### Ablation table

| Condition | Description |
|-----------|-------------|
| A — Baseline | Current FullStrategy, no structural prior |
| B — Cluster label only | Cluster label injected into prompt, no affinity scoring |
| C — Affinity scoring only | Structural re-ranking, no prompt injection |
| D — Full sketch ($\alpha=0.5$) | Cluster label + affinity scoring combined |
| E — Full sketch + waypoints | D + cluster-path replanning at strategic level |

### Metrics
- **Primary:** % games solved in ≤30 steps on hard instances (N=500).
- **Secondary:** Mean steps on success; % games with ≥2 repeated articles (loop rate); total LLM tokens consumed.
- **Diagnostic:** Spearman $\rho(\hat{C}, d^*)$ — must be ≥0.3 before proceeding.

### Timeline
| Task | Duration |
|------|----------|
| Graph extraction + filtering | 1 day |
| GraphSAGE training | 2–3 days |
| Clustering + commute-time matrix | 1 day |
| Validation gate | 2 hours |
| Harness integration | 2 days |
| Ablation runs (500 games × 5 conditions) | 2 days |
| **Total** | **~10 days** |

---

## Revised novelty framing

Individual components (GNN clustering, commute-time) are established. Novelty is in the combination:

1. **Offline structural oracle for LLM navigation**: existing Graph-RAG and LLM+KG work always queries the graph at inference time. Pre-computing and caching a compressed structural oracle is a different engineering trade-off — zero inference-time graph access, no API overhead.

2. **Cluster-level A\* waypoints for LLM prompting**: no prior work uses cluster-level search to provide intermediate goals for an LLM navigator. The closest analogue is Feudal Networks (Nachum et al., 2018) in RL, but that requires differentiable training.

3. **Commute-time as WikiRace navigability proxy**: if the validation gate confirms $\rho \geq 0.3$, this is the first empirical demonstration that random-walk structural distance predicts WikiRace path quality — a result of independent value to the graph ML community.

---

## References
- Hamilton et al. (2017), arXiv:1706.02216 — GraphSAGE
- Razeghi et al. (2026), arXiv:2602.16902 — LLM-WikiRace Benchmark
- He et al. (2024), arXiv:2410.14211 — Paths-over-Graph
- Nachum et al. (2018), arXiv:1805.08296 — HIRO hierarchical RL
- LLM-GNN integration survey (2024), arXiv:2412.19211
