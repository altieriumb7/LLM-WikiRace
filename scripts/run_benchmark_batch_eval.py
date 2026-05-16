#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from dataclasses import dataclass
from typing import Any

try:
    from LLM_wikirace import LLMInferenceEngine, WikiRaceEvaluator
except Exception as exc:
    raise SystemExit(
        "Missing dependency 'LLM_wikirace'. Install the official benchmark package first. "
        f"Original import error: {exc}"
    )

from wikirace.config import load_mode
from wikirace.benchmark_adapter import BenchmarkStateAdapter, validate_batch_contract


@dataclass
class _Candidate:
    page: str
    estimated_dist: int = 1


class TheoryDrivenBatchEngine(LLMInferenceEngine):
    """Benchmark-compatible engine for the local LLM-WikiRace navigation modes."""

    def __init__(self, mode: str, budget: int = 30, seed: int = 42):
        super().__init__(model_name=f"theory-{mode}", model_seed=seed)
        self.mode = mode
        self.budget = budget
        self.state_adapter = BenchmarkStateAdapter()

    def _choose_index(self, gs: Any) -> int:
        view = self.state_adapter.to_view(gs)
        outgoing = list(view.outgoing_links)

        if not outgoing:
            return 0

        if self.mode == "baseline":
            return 0

        visited = set(view.visited_pages)
        steps_used = int(view.steps_used)

        ranked = [_Candidate(page=x, estimated_dist=1) for x in outgoing]

        for cand in ranked:
            if cand.page in visited:
                continue
            if steps_used + 1 + cand.estimated_dist > self.budget:
                continue
            return outgoing.index(cand.page)

        for i, page in enumerate(outgoing):
            if page not in visited:
                return i

        return 0

    def batch_ask_for_choice(self, game_states):
        answers: list[int] = []
        raws: list[str] = []
        usage: list[dict[str, int]] = []

        for gs in game_states:
            choice = self._choose_index(gs)
            answers.append(choice)
            raws.append(f"I choose {choice}")
            usage.append({"output_tokens": 1})

        validate_batch_contract(answers, raws, usage, game_states)
        return answers, raws, usage, game_states


def parse_game_ids(raw: str | None, limit: int | None) -> list[int] | None:
    if raw:
        return [int(x.strip()) for x in raw.split(",") if x.strip()]
    if limit is not None:
        return list(range(limit))
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode-config", default="configs/modes/full.yaml")
    ap.add_argument("--difficulty", default="easy", choices=["easy", "medium", "hard"])
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--log-save-path", default="game_logs")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--wikigraph-path", required=True)
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--game-ids", default=None, help="Comma-separated game IDs, e.g. 0,1,2")
    ap.add_argument("--max-path-length", type=int, default=30)
    ap.add_argument("--max-choices", type=int, default=50)
    args = ap.parse_args()

    cfg = load_mode(Path(args.mode_config))
    game_ids = parse_game_ids(args.game_ids, args.limit)

    engine = TheoryDrivenBatchEngine(mode=cfg.strategy, budget=cfg.budget, seed=args.seed)

    evaluator = WikiRaceEvaluator(
        inference_engine=engine,
        difficulty=args.difficulty,
        game_ids=game_ids,
        batch_size=args.batch_size,
        log_save_path=args.log_save_path,
        wikigraph_path=args.wikigraph_path,
        max_path_length=args.max_path_length,
        max_choices=args.max_choices,
        seed=args.seed,
    )

    evaluator.evaluate()


if __name__ == "__main__":
    main()
