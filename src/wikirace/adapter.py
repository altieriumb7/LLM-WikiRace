import json, os, time, random
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Literal, Optional
from urllib import request, error
from urllib.parse import quote

class AdapterError(RuntimeError): ...

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
    def __init__(self, base_url=None, timeout_seconds: int = 20, max_retries: int = 3):
        self.base_url = base_url or os.getenv('WIKIRACE_API_BASE_URL')
        if not self.base_url: raise AdapterError('Missing WIKIRACE_API_BASE_URL')
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
    def _get(self, path):
        url=self.base_url.rstrip('/')+path
        delay=1
        for _ in range(self.max_retries):
            try:
                with request.urlopen(url, timeout=self.timeout_seconds) as r:
                    raw=r.read().decode('utf-8')
                    try: return json.loads(raw)
                    except Exception: raise AdapterError(f'malformed_json raw={raw[:200]}')
            except error.HTTPError as e:
                if e.code==429:
                    time.sleep(delay+random.random()); delay*=2; continue
                raise AdapterError(f'http_error status={e.code}')
        raise AdapterError('rate_limited')
    def get_instances(self, difficulty, limit):
        return self._get(f'/instances?split=live&difficulty={difficulty}&limit={limit}')
    def get_game_instances(self, split: str, difficulty: str, limit: int) -> List[GameInstance]:
        data = self._get(f'/instances?split={split}&difficulty={difficulty}&limit={limit}')
        return [GameInstance(**x) for x in data]
    def get_outgoing_links(self, page):
        safe_page = quote(str(page), safe="")
        links=self._get(f'/page/{safe_page}/links').get('outgoing_links',[])
        if links==[]:
            print({'warning':'dead_end_detected','page':page,'timestamp':datetime.utcnow().isoformat()})
        return links
    def get_page_metrics(self, page: str) -> PageMetrics:
        safe_page = quote(str(page), safe="")
        try:
            data = self._get(f'/page/{safe_page}/metrics')
            return PageMetrics(page=page, out_degree=data.get("out_degree"), pagerank=data.get("pagerank"))
        except AdapterError:
            links = self.get_outgoing_links(page)
            return PageMetrics(page=page, out_degree=len(links), pagerank=None)
    def get_link_metrics(self, pages: List[str]) -> Dict[str, PageMetrics]:
        return {p: self.get_page_metrics(p) for p in pages}
    def is_target(self, current, target): return current==target
