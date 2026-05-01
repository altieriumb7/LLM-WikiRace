from __future__ import annotations

import sqlite3
from pathlib import Path


class DistanceOracle:
    """
    Exact shortest-path distance lookup on a precomputed Wikipedia hyperlink graph.
    """

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_distances_target_source
            ON distances(target, source)
            """
        )
        self.conn.commit()

    def distance(self, source: str, target: str) -> int | None:
        cursor = self.conn.execute(
            """
            SELECT dist
            FROM distances
            WHERE target = ?
              AND source = ?
            """,
            (target, source),
        )
        row = cursor.fetchone()
        return int(row[0]) if row else None

    def batch_distance(self, sources: list[str], target: str) -> dict[str, int | None]:
        if not sources:
            return {}

        placeholders = ",".join("?" for _ in sources)
        cursor = self.conn.execute(
            f"""
            SELECT source, dist
            FROM distances
            WHERE target = ?
              AND source IN ({placeholders})
            """,
            (target, *sources),
        )

        found = {source: int(dist) for source, dist in cursor.fetchall()}
        return {source: found.get(source) for source in sources}

    def close(self) -> None:
        self.conn.close()
