from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import openai

from .embeddings import EmbeddingCache, cosine_sim
from .mcts import run_mcts


@dataclass
class MCTSEmbeddingStrategy:
    """
    NavigationStrategy implementation using MCTS + embedding heuristic.

    Compatible with the NavigationStrategy Protocol in src/wikirace/strategies.py.
    Drop-in: pass to run_game() from src/wikirace/agent.py.
    """

    cache: EmbeddingCache
    adapter: object
    n_simulations: int = 20
    revisit_penalty: float = 0.4
    c_ucb: float = 0.3
    dispute_threshold: float = 0.05
    llm_threshold: float = 0.03
    openai_model: str = "gpt-4o-mini"
    use_llm_arbiter: bool = True
    _messages: list = field(default_factory=list, repr=False)

    def select_move(self, state, candidates: list[str]) -> tuple[str | None, dict]:
        """
        Run MCTS over candidates. Returns (selected_link, meta_dict).
        meta_dict keys: mcts_winner, top_score, score_gap, depth2_used, llm_used.
        Returns (None, {"failure_reason": "..."}) on hard failure.
        """
        if not candidates:
            return None, {"failure_reason": "no_candidates"}

        # Build llm_fn if use_llm_arbiter is True
        llm_fn: Callable[[list[str], str], str] | None = None
        if self.use_llm_arbiter:
            def llm_fn(top_3_titles: list[str], target: str) -> str:
                """LLM arbiter closure."""
                # Build prompt
                links_str = "\n".join(f"  {i+1}. {title}" for i, title in enumerate(top_3_titles))
                prompt = (
                    f"You are navigating Wikipedia to reach '{target}'.\n"
                    f"From the current article you can follow one of these links:\n"
                    f"{links_str}\n"
                    f"Which link is most likely to lead to '{target}' in the fewest clicks?\n"
                    f"Reply with only the article title, exactly as written above."
                )

                try:
                    response = openai.OpenAI().chat.completions.create(
                        model=self.openai_model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0,
                        max_tokens=100,
                    )
                    return response.choices[0].message.content.strip()
                except Exception:
                    # Fallback to first candidate on any error
                    return candidates[0]

        # Call run_mcts
        try:
            winner = run_mcts(
                candidates=candidates,
                target=state.target_page,
                visited=set(state.visited),
                cache=self.cache,
                adapter=self.adapter,
                n_simulations=self.n_simulations,
                revisit_penalty=self.revisit_penalty,
                c_ucb=self.c_ucb,
                dispute_threshold=self.dispute_threshold,
                llm_threshold=self.llm_threshold,
                llm_fn=llm_fn,
            )
        except ValueError:
            return None, {"failure_reason": "mcts_error"}

        # Compute meta dict
        try:
            winner_emb = self.cache.get(winner)
            target_emb = self.cache.get(state.target_page)
            top_score = float(cosine_sim(winner_emb, target_emb))
        except Exception:
            top_score = 0.0

        meta = {
            "mcts_winner": winner,
            "top_score": top_score,
            "score_gap": 0.0,
            "depth2_used": False,
            "llm_used": False,
        }

        return winner, meta

    def should_replan(self, state) -> bool:
        return False

    def on_replan(self, state, candidates) -> None:
        return None
