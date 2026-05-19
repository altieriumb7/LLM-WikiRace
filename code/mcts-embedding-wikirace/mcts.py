from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable

from .embeddings import EmbeddingCache, cosine_sim


@dataclass
class MCTSNode:
    title: str
    visits: int = 0
    value_sum: float = 0.0
    children: dict[str, MCTSNode] = field(default_factory=dict)

    @property
    def value(self) -> float:
        if self.visits == 0:
            return 0.0
        return self.value_sum / self.visits

    def ucb(self, parent_visits: int, c: float) -> float:
        if self.visits == 0:
            return math.inf
        return self.value + c * math.sqrt(math.log(parent_visits) / self.visits)


def run_mcts(
    candidates: list[str],
    target: str,
    visited: set[str],
    cache: EmbeddingCache,
    adapter,
    n_simulations: int = 20,
    revisit_penalty: float = 0.4,
    c_ucb: float = 0.3,
    dispute_threshold: float = 0.05,
    llm_threshold: float = 0.03,
    llm_fn: Callable[[list[str], str], str] | None = None,
) -> str:
    if not candidates:
        raise ValueError("candidates list cannot be empty")

    nodes: dict[str, MCTSNode] = {title: MCTSNode(title=title) for title in candidates}

    target_emb = cache.get(target)
    candidate_embeddings = cache.get_batch(candidates)

    for _ in range(n_simulations):
        unvisited = [node for node in nodes.values() if node.visits == 0]
        if unvisited:
            selected_node = unvisited[0]
        else:
            total_visits = sum(node.visits for node in nodes.values())
            selected_node = max(
                nodes.values(),
                key=lambda node: node.ucb(total_visits, c_ucb)
            )

        candidate_emb = candidate_embeddings[selected_node.title]
        score = cosine_sim(candidate_emb, target_emb)

        if selected_node.title in visited:
            score -= revisit_penalty

        selected_node.visits += 1
        selected_node.value_sum += score

    sorted_nodes = sorted(nodes.values(), key=lambda node: node.value, reverse=True)

    top1 = sorted_nodes[0]
    top2 = sorted_nodes[1] if len(sorted_nodes) > 1 else None
    top3_nodes = sorted_nodes[:3] if len(sorted_nodes) >= 3 else sorted_nodes

    gap = top1.value - top2.value if top2 else 0.0

    if gap < dispute_threshold and adapter is not None and len(sorted_nodes) > 1:
        depth2_scores: dict[str, float] = {}

        for node in top3_nodes:
            max_depth2_score = 0.0
            try:
                links = adapter.get_outgoing_links(node.title)
                if links:
                    link_embeddings = cache.get_batch(links)
                    for link in links:
                        if link in link_embeddings:
                            link_emb = link_embeddings[link]
                            sim = cosine_sim(link_emb, target_emb)
                            max_depth2_score = max(max_depth2_score, sim)
            except Exception:
                pass

            depth2_scores[node.title] = max_depth2_score

        top3_nodes = sorted(
            top3_nodes,
            key=lambda node: depth2_scores.get(node.title, 0.0),
            reverse=True
        )
        top1 = top3_nodes[0]
        top2 = top3_nodes[1] if len(top3_nodes) > 1 else None
        gap = depth2_scores.get(top1.title, 0.0) - depth2_scores.get(top2.title, 0.0) if top2 else 0.0

    if gap < llm_threshold and llm_fn is not None:
        top3_titles = [node.title for node in top3_nodes[:3]]
        result = llm_fn(top3_titles, target)
        if result in candidates:
            return result

    return top1.title
