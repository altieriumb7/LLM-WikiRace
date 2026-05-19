import json
import os
import tempfile
from pathlib import Path

import numpy as np
from openai import OpenAI


class EmbeddingCache:
    """
    Lazy, disk-persistent cache: article title -> np.ndarray[float32, shape=(1536,)]
    Backed by ~/.wikirace_embed_cache.json (lists of floats).
    Uses OpenAI text-embedding-3-small.
    Thread-safe: file is written atomically on each miss.
    """

    def __init__(
        self, cache_path: str | None = None, model: str = "text-embedding-3-small"
    ) -> None:
        self.model = model
        self.cache_path = Path(cache_path or "~/.wikirace_embed_cache.json").expanduser()
        self.cache: dict[str, list[float]] = {}
        self.client = OpenAI()

        if self.cache_path.exists():
            with open(self.cache_path, "r") as f:
                self.cache = json.load(f)

    def get(self, title: str) -> np.ndarray:
        """Return embedding for one title. Blocks on API call on cache miss."""
        if title in self.cache:
            return np.array(self.cache[title], dtype=np.float32)

        response = self.client.embeddings.create(
            model=self.model,
            input=[title],
        )
        embedding = response.data[0].embedding
        self.cache[title] = embedding
        self._write_cache_atomically()
        return np.array(embedding, dtype=np.float32)

    def get_batch(self, titles: list[str]) -> dict[str, np.ndarray]:
        """Return embeddings for multiple titles. Batches misses into one API call."""
        result = {}
        misses = []
        miss_indices = {}

        for title in titles:
            if title in self.cache:
                result[title] = np.array(self.cache[title], dtype=np.float32)
            else:
                miss_indices[title] = len(misses)
                misses.append(title)

        if misses:
            for batch_start in range(0, len(misses), 100):
                batch_end = min(batch_start + 100, len(misses))
                batch = misses[batch_start:batch_end]

                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch,
                )

                for item in response.data:
                    title = batch[item.index]
                    embedding = item.embedding
                    self.cache[title] = embedding
                    result[title] = np.array(embedding, dtype=np.float32)

            self._write_cache_atomically()

        return result

    def _write_cache_atomically(self) -> None:
        """Write cache to disk atomically using a temporary file."""
        parent_dir = self.cache_path.parent
        parent_dir.mkdir(parents=True, exist_ok=True)

        fd, tmp_path = tempfile.mkstemp(
            dir=parent_dir,
            prefix=".tmp_",
            suffix=".json",
        )
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(self.cache, f)
            os.replace(tmp_path, self.cache_path)
        except Exception:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
            raise


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    """Return cosine similarity in [-1, 1]. Returns 0.0 if either vector is zero."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return float(np.dot(a, b) / (norm_a * norm_b))
