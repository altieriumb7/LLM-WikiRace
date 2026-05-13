import json
from urllib.error import HTTPError

import pytest

from wikirace.adapter import AdapterError, WikiRaceAdapter


class Response:
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self): return json.dumps({"outgoing_links": ["B"]}).encode()


def test_adapter_quotes_page_titles_and_uses_timeout(monkeypatch):
    seen = {}
    def fake_urlopen(url, timeout):
        seen["url"] = url
        seen["timeout"] = timeout
        return Response()
    monkeypatch.setattr("wikirace.adapter.request.urlopen", fake_urlopen)
    adapter = WikiRaceAdapter(base_url="https://example.test", timeout_seconds=7)
    assert adapter.get_outgoing_links("A B/C") == ["B"]
    assert seen == {"url": "https://example.test/page/A%20B%2FC/links", "timeout": 7}


def test_adapter_non_retry_http_error(monkeypatch):
    def fake_urlopen(url, timeout):
        raise HTTPError(url, 404, "missing", hdrs=None, fp=None)
    monkeypatch.setattr("wikirace.adapter.request.urlopen", fake_urlopen)
    with pytest.raises(AdapterError):
        WikiRaceAdapter(base_url="https://example.test").get_instances("easy", 1)
