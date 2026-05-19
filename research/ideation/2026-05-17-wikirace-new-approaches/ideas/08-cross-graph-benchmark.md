# Cross-Graph Adversarial WikiRace: Multilingual + Wikidata + Temporal

## One-line summary
Extend WikiRace from English Wikipedia's static link graph to a triple-modality benchmark spanning Wikidata entity graphs, multilingual Wikipedia editions, and time-sliced graph snapshots, forcing evaluation of navigation strategy generalization.

## Problem it solves
LLM-WikiRace benchmarks only English Wikipedia in a fixed link structure, making it impossible to distinguish learned navigation strategies from memorized Wikipedia topology. The 23% hard-instance failure rate may be Wikipedia-specific brittleness, not general planning failure.

## Method
Build 3-axis evaluation suite (same task: source → target in K steps):

1. **Wikidata axis**: entity-property graph navigation. 500 adversarially hard pairs (cross-type hierarchies, inverse properties).
2. **Multilingual axis**: German, French, Japanese, Arabic Wikipedia + "pivot" set where English paths are blocked.
3. **Temporal axis**: Wikipedia snapshots 2015/2018/2023/2026. "Retroactive" set: 2026 source/target, only 2015 graph.

Adversarial pair selection by graph edit distance variance (high variance across modalities = hard).

## Key novelty
- First cross-modality knowledge graph navigation benchmark
- Adversarial pair selection by graph variance (not human intuition)
- Temporal element reveals topology overfitting
- Directly tests replanning under graph structure change

## Feasibility notes
- Data: all sources public (Wikidata dumps, Wikipedia snapshots, multilingual editions)
- Assembly: 2–3 weeks
- Eval: reuse WikiRace BFS oracle
- Total: 6–8 weeks

## Risks / open questions
1. Wikidata sparsity may make many instances infeasible (need K=50)
2. Multilingual link quality varies (language quality bias)
3. Wikipedia 2015 snapshot reconstruction is hard
4. Models failing on Wikidata may be format-unfamiliar, not strategically weak

## Axis: Benchmark extension / new evaluation
