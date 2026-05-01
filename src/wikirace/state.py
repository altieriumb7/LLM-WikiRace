from dataclasses import dataclass, field
from typing import Tuple, FrozenSet

@dataclass(frozen=True)
class GameState:
    current_page: str
    target_page: str
    steps_used: int
    budget: int
    path: Tuple[str, ...]
    visited: FrozenSet[str] = field(default_factory=frozenset)

    def next(self, page: str) -> 'GameState':
        return GameState(page, self.target_page, self.steps_used + 1, self.budget, self.path + (page,), self.visited | {page})

@dataclass(frozen=True)
class Link:
    page: str
