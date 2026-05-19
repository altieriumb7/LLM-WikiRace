"""
CLI entry point for MCTS + Embedding-based WikiRace navigator.

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

import sys
import os
import json
import argparse
from typing import Any

import numpy as np

# Setup paths for imports
_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(_HERE, "..", "..", "src")
sys.path.insert(0, _SRC)

# Register package so relative imports work
import importlib.util
import types

pkg = types.ModuleType("mcts_embedding_wikirace")
pkg.__path__ = [_HERE]
pkg.__package__ = "mcts_embedding_wikirace"
sys.modules["mcts_embedding_wikirace"] = pkg

from mcts_embedding_wikirace.embeddings import EmbeddingCache, cosine_sim
from mcts_embedding_wikirace.mcts import MCTSNode, run_mcts
from mcts_embedding_wikirace.strategy import MCTSEmbeddingStrategy
from wikirace.adapter import WikiRaceAdapter
from wikirace.agent import run_game


# Mock adapter for smoke tests
MOCK_GRAPH = {
    "Python (programming language)": ["Guido van Rossum", "Programming language", "Software"],
    "Guido van Rossum": ["Netherlands", "Python (programming language)", "Programmer"],
    "Programming language": ["Computer science", "Software", "Algorithm"],
    "Software": ["Computer", "Algorithm", "Mahatma Gandhi"],
    "Computer science": ["Algorithm", "Mathematics", "Mahatma Gandhi"],
    "Algorithm": ["Mathematics", "Computer science", "Mahatma Gandhi"],
    "Mathematics": ["Mahatma Gandhi", "Science", "Algorithm"],
    "Mahatma Gandhi": [],
    "Netherlands": ["Europe", "Amsterdam"],
    "Programmer": ["Software", "Computer science"],
    "Computer": ["Software", "Algorithm"],
    "Science": ["Mathematics", "Mahatma Gandhi"],
    "Europe": ["Netherlands", "Germany"],
    "Amsterdam": ["Netherlands"],
    "Germany": ["Europe"],
}


class MockAdapter:
    """Mock WikiRaceAdapter that uses a hardcoded graph."""

    def get_outgoing_links(self, page: str) -> list[str]:
        """Return outgoing links for a page from the mock graph."""
        return MOCK_GRAPH.get(page, [])

    def is_target(self, current: str, target: str) -> bool:
        """Check if current page is the target."""
        return current == target


class MockEmbeddingCache:
    """Mock EmbeddingCache that generates deterministic random embeddings."""

    def get(self, title: str) -> np.ndarray:
        """Return a deterministic embedding for a title."""
        rng = np.random.default_rng(abs(hash(title)) % (2**32))
        return rng.random(1536).astype(np.float32)

    def get_batch(self, titles: list[str]) -> dict[str, np.ndarray]:
        """Return embeddings for multiple titles."""
        return {t: self.get(t) for t in titles}


def smoke_test() -> int:
    """Run a smoke test with mock adapter and cache."""
    print("Running smoke test...")

    mock_adapter = MockAdapter()
    mock_cache = MockEmbeddingCache()

    strategy = MCTSEmbeddingStrategy(
        cache=mock_cache,
        adapter=mock_adapter,
        n_simulations=5,
        use_llm_arbiter=False,
    )

    result = run_game(
        "Python (programming language)",
        "Mahatma Gandhi",
        strategy,
        mock_adapter,
        budget=10,
    )

    print(f"Status: {result['status']}")
    print(f"Steps used: {result['state'].steps_used}")

    if result["status"] == "success":
        print("Smoke test PASSED")
        return 0
    else:
        print(f"Smoke test FAILED: {result.get('failure_reason', 'unknown')}")
        return 1


def single_game(start: str, target: str, steps: int = 30, sims: int = 20) -> int:
    """Run a single live game."""
    print(f"Running single game: {start} -> {target}")
    print(f"  Budget: {steps} steps")
    print(f"  Simulations per step: {sims}")

    # Check for required env vars
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable not set")
        return 1

    base_url = os.getenv("WIKIRACE_API_BASE_URL")
    if not base_url:
        print("ERROR: WIKIRACE_API_BASE_URL environment variable not set")
        return 1

    try:
        adapter = WikiRaceAdapter(base_url=base_url)
        cache = EmbeddingCache()
        strategy = MCTSEmbeddingStrategy(
            cache=cache,
            adapter=adapter,
            n_simulations=sims,
        )

        result = run_game(
            start,
            target,
            strategy,
            adapter,
            budget=steps,
        )

        output = {
            "status": result["status"],
            "steps_used": result["state"].steps_used,
            "failure_reason": result.get("failure_reason"),
        }
        print(json.dumps(output, indent=2))

        return 0 if result["status"] == "success" else 1
    except Exception as e:
        print(f"ERROR: {e}")
        return 1


def benchmark(n: int = 10, difficulty: str = "easy") -> int:
    """Run a benchmark with N games."""
    print(f"Running benchmark: {n} games at {difficulty} difficulty")

    # Check for required env vars
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable not set")
        return 1

    base_url = os.getenv("WIKIRACE_API_BASE_URL")
    if not base_url:
        print("ERROR: WIKIRACE_API_BASE_URL environment variable not set")
        return 1

    try:
        adapter = WikiRaceAdapter(base_url=base_url)
        cache = EmbeddingCache()

        # Fetch game instances
        print(f"Fetching {n} game instances...")
        instances = adapter.get_game_instances(split="live", difficulty=difficulty, limit=n)
        print(f"Fetched {len(instances)} instances")

        successes = 0
        total_steps_on_success = 0
        failures = 0

        for i, instance in enumerate(instances, 1):
            print(f"\n[{i}/{len(instances)}] {instance.start_page} -> {instance.target_page}")

            try:
                strategy = MCTSEmbeddingStrategy(
                    cache=cache,
                    adapter=adapter,
                    n_simulations=20,
                )

                result = run_game(
                    instance.start_page,
                    instance.target_page,
                    strategy,
                    adapter,
                    budget=30,
                )

                if result["status"] == "success":
                    successes += 1
                    total_steps_on_success += result["state"].steps_used
                    print(f"  SUCCESS in {result['state'].steps_used} steps")
                else:
                    failures += 1
                    print(f"  FAILED: {result.get('failure_reason')}")
            except Exception as e:
                failures += 1
                print(f"  ERROR: {e}")

        # Print summary
        print("\n" + "=" * 60)
        print("BENCHMARK RESULTS")
        print("=" * 60)
        print(f"Total games: {len(instances)}")
        print(f"Successes: {successes}")
        print(f"Failures: {failures}")
        print(f"Success rate: {100.0 * successes / len(instances):.1f}%")
        if successes > 0:
            avg_steps = total_steps_on_success / successes
            print(f"Mean steps on success: {avg_steps:.1f}")
        print("=" * 60)

        return 0
    except Exception as e:
        print(f"ERROR: {e}")
        return 1


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="MCTS + Embedding-based WikiRace navigator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run smoke test with mock adapter (default if no args given)",
    )

    parser.add_argument(
        "--start",
        type=str,
        help="Start article for single-game mode",
    )

    parser.add_argument(
        "--target",
        type=str,
        help="Target article for single-game mode",
    )

    parser.add_argument(
        "--steps",
        type=int,
        default=30,
        help="Budget (max steps) for single-game mode (default: 30)",
    )

    parser.add_argument(
        "--sims",
        type=int,
        default=20,
        help="Number of MCTS simulations per step (default: 20)",
    )

    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run benchmark mode",
    )

    parser.add_argument(
        "--n",
        type=int,
        default=10,
        help="Number of games for benchmark mode (default: 10)",
    )

    parser.add_argument(
        "--difficulty",
        type=str,
        choices=["easy", "medium", "hard"],
        default="easy",
        help="Difficulty level for benchmark (default: easy)",
    )

    args = parser.parse_args()

    # Determine mode
    if args.benchmark:
        return benchmark(n=args.n, difficulty=args.difficulty)
    elif args.start and args.target:
        return single_game(args.start, args.target, steps=args.steps, sims=args.sims)
    else:
        # Default to smoke test
        return smoke_test()


if __name__ == "__main__":
    sys.exit(main())
