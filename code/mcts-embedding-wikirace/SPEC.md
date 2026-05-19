# SPEC — MCTS + Embedding Heuristic Navigator

## Purpose
A drop-in `NavigationStrategy` implementation for the LLM-WikiRace harness that
replaces greedy LLM link ranking with Monte Carlo Tree Search guided by OpenAI
embedding similarity. Requires only `OPENAI_API_KEY` and the existing WikiRace
adapter. Zero local GPU training.

---

## File layout

```
code/mcts-embedding-wikirace/
├── SPEC.md              # this file
├── embeddings.py        # EmbeddingCache — OpenAI text-embedding-3-small, disk-persistent
├── mcts.py              # MCTSNode + run_mcts()
├── strategy.py          # MCTSEmbeddingStrategy (NavigationStrategy Protocol)
├── run.py               # CLI smoke test + single-game runner
└── requirements.txt     # openai>=1.0.0, numpy>=1.24
```

---

## Shared interfaces (all files must match exactly)

### embeddings.py

```python
import numpy as np

class EmbeddingCache:
    """
    Lazy, disk-persistent cache: article title -> np.ndarray[float32, shape=(1536,)]
    Backed by ~/.wikirace_embed_cache.json (base64-encoded vectors).
    Uses OpenAI text-embedding-3-small.
    Thread-safe: file is written atomically on each miss.
    """
    def __init__(self, cache_path: str | None = None, model: str = "text-embedding-3-small") -> None: ...

    def get(self, title: str) -> np.ndarray:
        """Return embedding for one title. Blocks on API call on cache miss."""
        ...

    def get_batch(self, titles: list[str]) -> dict[str, np.ndarray]:
        """Return embeddings for multiple titles. Batches misses into one API call."""
        ...

def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    """Return cosine similarity in [-1, 1]. Returns 0.0 if either vector is zero."""
    ...
```

### mcts.py

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable
from .embeddings import EmbeddingCache

@dataclass
class MCTSNode:
    title: str
    visits: int = 0
    value_sum: float = 0.0
    children: dict[str, "MCTSNode"] = field(default_factory=dict)

    @property
    def value(self) -> float:
        """Mean value. Returns 0.0 if unvisited."""
        ...

    def ucb(self, parent_visits: int, c: float) -> float:
        """UCB1 score. Returns +inf for unvisited nodes."""
        ...


def run_mcts(
    candidates: list[str],
    target: str,
    visited: set[str],
    cache: EmbeddingCache,
    adapter,                              # WikiRaceAdapter | None — used for depth-2 expansion
    n_simulations: int = 20,
    revisit_penalty: float = 0.4,
    c_ucb: float = 0.3,
    dispute_threshold: float = 0.05,     # gap below which depth-2 lookahead fires
    llm_threshold: float = 0.03,         # gap below which LLM arbiter fires
    llm_fn: Callable[[list[str], str], str] | None = None,
) -> str:
    """
    Run MCTS over `candidates` and return the selected article title.

    Algorithm:
    1. Build MCTSNode for each candidate.
    2. For n_simulations iterations:
       a. Select candidate via UCB (treat root as a virtual node with all candidates as children).
       b. Score = cosine_sim(embed(candidate), embed(target)) - revisit_penalty if in visited.
       c. Backprop: node.visits += 1, node.value_sum += score.
    3. Rank candidates by node.value (descending).
    4. If top-1.value - top-2.value < dispute_threshold AND adapter is not None:
       - Fetch real outgoing links for top-3 candidates (adapter.get_outgoing_links).
       - For each, compute max cosine_sim among their children embeddings (depth-2 lookahead).
       - Re-rank using depth-2 max score.
    5. If gap still < llm_threshold AND llm_fn is not None:
       - Call llm_fn(top_3_titles, target) -> selected title.
       - Return that title if valid, else fall back to top-1 by value.
    6. Return top-ranked candidate.

    Raises ValueError if candidates is empty.
    """
    ...
```

### strategy.py

```python
from dataclasses import dataclass, field
from .embeddings import EmbeddingCache
from .mcts import run_mcts

@dataclass
class MCTSEmbeddingStrategy:
    """
    NavigationStrategy implementation using MCTS + embedding heuristic.

    Compatible with the NavigationStrategy Protocol in src/wikirace/strategies.py.
    Drop-in: pass to run_game() from src/wikirace/agent.py.
    """
    cache: EmbeddingCache
    adapter: object                        # WikiRaceAdapter — for depth-2 expansion
    n_simulations: int = 20
    revisit_penalty: float = 0.4
    c_ucb: float = 0.3
    dispute_threshold: float = 0.05
    llm_threshold: float = 0.03
    openai_model: str = "gpt-4o-mini"     # used for LLM arbiter
    use_llm_arbiter: bool = True
    _messages: list = field(default_factory=list, repr=False)

    def select_move(self, state, candidates: list[str]) -> tuple[str | None, dict]:
        """
        Run MCTS over candidates. Returns (selected_link, meta_dict).
        meta_dict keys: mcts_winner, top_score, score_gap, depth2_used, llm_used.
        Returns (None, {"failure_reason": "..."}) on hard failure.
        """
        ...

    def should_replan(self, state) -> bool:
        return False

    def on_replan(self, state, candidates) -> None:
        return None
```

### run.py

```python
"""
CLI entry point.

Usage:
  python run.py --smoke
      Runs a single hard-coded game (start="Python (programming language)",
      target="Mahatma Gandhi") for up to 10 steps using mock adapter.
      Exits 0 on success, 1 on failure.

  python run.py --start ARTICLE --target ARTICLE [--steps N] [--sims N]
      Runs one live game via WikiRace adapter (requires WIKIRACE_API_BASE_URL).

  python run.py --benchmark [--n N] [--difficulty easy|medium|hard]
      Runs N games and prints a results table.
"""
```

---

## Algorithm detail

### Embedding similarity as heuristic

$$h(u, t) = \cos(\mathbf{e}_u,\, \mathbf{e}_t) = \frac{\mathbf{e}_u \cdot \mathbf{e}_t}{\|\mathbf{e}_u\| \|\mathbf{e}_t\|}$$

Higher = better (article $u$ is closer in embedding space to target $t$).

### UCB selection

$$\text{UCB}(i) = \bar{h}_i + c\sqrt{\frac{\ln N}{N_i}}$$

where $N$ = total simulations so far, $N_i$ = visits to candidate $i$, $c=0.3$.
Unvisited nodes get $\text{UCB} = +\infty$ (always expand first).

### Revisit penalty

$$\tilde{h}(u, t) = h(u, t) - p \cdot \mathbf{1}[u \in \text{visited}]$$

$p = 0.4$ by default (tuneable via `revisit_penalty`).

### Depth-2 lookahead (fires when score gap < `dispute_threshold`)

For each of the top-3 candidates $u$:
1. Fetch $\text{Links}(u)$ via `adapter.get_outgoing_links(u)`.
2. Compute $H_2(u) = \max_{v \in \text{Links}(u)} h(v, t)$.
3. Re-rank by $H_2(u)$.

This costs 3 adapter API calls per disputed step.

### LLM arbiter (fires when gap still < `llm_threshold`)

Prompt sent to `gpt-4o-mini`:
```
You are navigating Wikipedia to reach "[target]".
From the current article you can follow one of these links:
  1. [candidate_1]
  2. [candidate_2]
  3. [candidate_3]
Which link is most likely to lead to "[target]" in the fewest clicks?
Reply with only the article title, exactly as written above.
```

---

## Cost estimates (per 30-step game)

| Component | Calls | Tokens (approx) | Cost (USD) |
|-----------|-------|-----------------|------------|
| Embeddings (3-small, new titles) | ~50 | ~2 500 | ~$0.000 05 |
| Depth-2 expansion (WikiRace API) | ~6 | — | free |
| LLM arbiter (gpt-4o-mini) | ~2 | ~300 | ~$0.000 15 |
| **Total** | | | **< $0.001** |

---

## Integration with existing harness

```python
import sys
sys.path.insert(0, "path/to/LLM-WikiRace/src")

from wikirace.adapter import WikiRaceAdapter
from wikirace.agent import run_game
from mcts_embedding_wikirace.embeddings import EmbeddingCache
from mcts_embedding_wikirace.strategy import MCTSEmbeddingStrategy

adapter = WikiRaceAdapter()
cache = EmbeddingCache()
strategy = MCTSEmbeddingStrategy(cache=cache, adapter=adapter)

result = run_game("Python (programming language)", "Mahatma Gandhi", strategy, adapter)
print(result["status"], result["state"].steps_used)
```

---

## Order of operations (build sequence)

1. `embeddings.py` — no deps; implement EmbeddingCache + cosine_sim
2. `requirements.txt` — list pinned deps
3. `mcts.py` — imports EmbeddingCache; implement MCTSNode + run_mcts
4. `strategy.py` — imports EmbeddingCache + run_mcts; implement MCTSEmbeddingStrategy
5. `run.py` — imports MCTSEmbeddingStrategy + WikiRaceAdapter; implement CLI
6. Smoke test: `python run.py --smoke` → exit 0

---

## Strongest objection

The depth-2 lookahead fetches 3 extra WikiRace API calls per disputed step.
On a 30-step game with 50% disputed steps, that is ~45 extra calls per game.
If the WikiRace API has rate limits or latency, this could slow games significantly.
Mitigation: the `adapter` parameter in `run_mcts` is optional (`None` disables
depth-2 lookahead entirely), falling back to depth-1 embedding-only selection.
