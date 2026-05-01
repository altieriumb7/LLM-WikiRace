import json, os, time, random
from datetime import datetime
from urllib import request, error

class AdapterError(RuntimeError): ...

class WikiRaceAdapter:
    def __init__(self, base_url=None):
        self.base_url = base_url or os.getenv('WIKIRACE_API_BASE_URL')
        if not self.base_url: raise AdapterError('Missing WIKIRACE_API_BASE_URL')
    def _get(self, path):
        url=self.base_url.rstrip('/')+path
        delay=1
        for _ in range(3):
            try:
                with request.urlopen(url) as r:
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
    def get_outgoing_links(self, page):
        links=self._get(f'/page/{page}/links').get('outgoing_links',[])
        if links==[]:
            print({'warning':'dead_end_detected','page':page,'timestamp':datetime.utcnow().isoformat()})
        return links
    def is_target(self, current, target): return current==target
