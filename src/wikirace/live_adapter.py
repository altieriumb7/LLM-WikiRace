from __future__ import annotations
import json, os, time
from dataclasses import dataclass
from typing import Dict, List, Literal, Optional
from urllib import request, error


@dataclass
class GameInstance:
    instance_id: str
    start_page: str
    target_page: str
    difficulty: Literal["easy", "medium", "hard"]


@dataclass
class PageMetrics:
    page: str
    out_degree: Optional[int]
    pagerank: Optional[float]


class WikiRaceAdapter:
    def __init__(self, base_url: Optional[str] = None, max_retries: int = 5, backoff_initial_seconds: int = 1, backoff_max_seconds: int = 30):
        self.base_url = base_url or os.getenv("WIKIRACE_API_BASE_URL")
        if not self.base_url:
            raise RuntimeError("Missing WIKIRACE_API_BASE_URL")
        self.max_retries = max_retries
        self.backoff_initial_seconds = backoff_initial_seconds
        self.backoff_max_seconds = backoff_max_seconds

    def _get(self, path: str):
        url = self.base_url.rstrip("/") + path
        delay = self.backoff_initial_seconds
        last_err = None
        for _ in range(self.max_retries):
            try:
                with request.urlopen(url) as resp:
                    return resp.status, json.loads(resp.read().decode("utf-8")), url
            except error.HTTPError as e:
                raw = e.read().decode("utf-8", errors="ignore")
                if e.code == 429 or 500 <= e.code < 600:
                    time.sleep(delay)
                    delay = min(self.backoff_max_seconds, delay * 2)
                    last_err = (e.code, raw, url)
                    continue
                raise RuntimeError(f"HTTP error page={path} status={e.code} raw={raw} endpoint={url}")
            except Exception as e:
                time.sleep(delay)
                delay = min(self.backoff_max_seconds, delay * 2)
                last_err = (None, str(e), url)
        raise RuntimeError(f"API retry exhausted endpoint={url} err={last_err}")

    def get_game_instances(self, split: str, difficulty: str, limit: int) -> List[GameInstance]:
        _, data, _ = self._get(f"/instances?split={split}&difficulty={difficulty}&limit={limit}")
        return [GameInstance(**x) for x in data]

    def get_outgoing_links(self, page: str) -> List[str]:
        status, data, url = self._get(f"/page/{page}/links")
        if "outgoing_links" not in data or not isinstance(data["outgoing_links"], list):
            raise RuntimeError(f"malformed API response page={page} endpoint={url} status={status} raw={data}")
        return data["outgoing_links"]

    def get_page_metrics(self, page: str) -> PageMetrics:
        try:
            _, data, _ = self._get(f"/page/{page}/metrics")
            return PageMetrics(page=page, out_degree=data.get("out_degree"), pagerank=data.get("pagerank"))
        except RuntimeError:
            links = self.get_outgoing_links(page)
            return PageMetrics(page=page, out_degree=len(links), pagerank=None)

    def get_link_metrics(self, pages: List[str]) -> Dict[str, PageMetrics]:
        return {p: self.get_page_metrics(p) for p in pages}

    def is_target(self, current_page: str, target_page: str) -> bool:
        return current_page == target_page
