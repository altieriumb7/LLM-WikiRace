# Distance Oracle (Proof of Concept)

This module adds an optional SQLite-backed exact distance lookup used only by `FullStrategy` when configured.

Expected schema:

```sql
CREATE TABLE distances (
  target TEXT NOT NULL,
  source TEXT NOT NULL,
  dist INTEGER NOT NULL,
  PRIMARY KEY(target, source)
);
```

Each row means: `source` can reach `target` in `dist` hyperlink steps.

An exact distance oracle turns WikiRace into greedy shortest-path following. This is a topology-access baseline, not an LLM reasoning improvement.

This PR is runtime integration only. It does **not** include full Wikipedia graph parsing.

Future work before full deployment:
- graph dump acquisition
- title normalization parity with adapter
- redirect handling
- reverse BFS generation
- SQLite build over full target set
- snapshot matching between benchmark and live adapter
