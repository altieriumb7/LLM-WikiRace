from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class BenchmarkStateView:
    outgoing_links: list[str]
    visited_pages: list[str]
    steps_used: int
    target_page: str | None = None
    current_page: str | None = None


class BenchmarkStateAdapter:
    """Normalize official benchmark GameState variants to a stable internal view."""

    OUTGOING_KEYS = ("outgoing_links", "links", "choices")
    VISITED_KEYS = ("visited_pages", "visited", "path", "history")
    STEPS_KEYS = ("steps_used", "step", "num_steps")
    TARGET_KEYS = ("target_page", "target", "goal")
    CURRENT_KEYS = ("current_page", "current", "page")

    @staticmethod
    def _read(obj: Any, keys: tuple[str, ...], default=None):
        for key in keys:
            if isinstance(obj, dict) and key in obj:
                return obj[key]
            if hasattr(obj, key):
                return getattr(obj, key)
        return default

    def to_view(self, game_state: Any) -> BenchmarkStateView:
        outgoing = self._read(game_state, self.OUTGOING_KEYS, default=[]) or []
        if not isinstance(outgoing, list):
            raise ValueError("GameState outgoing links must be a list")

        visited = self._read(game_state, self.VISITED_KEYS, default=[]) or []
        if not isinstance(visited, list):
            raise ValueError("GameState visited pages must be a list")

        steps = self._read(game_state, self.STEPS_KEYS, default=0) or 0
        try:
            steps_used = int(steps)
        except (TypeError, ValueError) as exc:
            raise ValueError("GameState steps_used must be an int-like value") from exc

        return BenchmarkStateView(
            outgoing_links=[str(x) for x in outgoing],
            visited_pages=[str(x) for x in visited],
            steps_used=steps_used,
            target_page=self._read(game_state, self.TARGET_KEYS),
            current_page=self._read(game_state, self.CURRENT_KEYS),
        )


def validate_batch_contract(answers, raw_answers, usage_data, game_states):
    n = len(game_states)
    if not (len(answers) == len(raw_answers) == len(usage_data) == n):
        raise ValueError("Batch output lengths are inconsistent")
    for i, a in enumerate(answers):
        if not isinstance(a, int):
            raise ValueError(f"Answer at index {i} is not int")
    for i, usage in enumerate(usage_data):
        if not isinstance(usage, dict):
            raise ValueError(f"Usage entry at index {i} is not a dict")
