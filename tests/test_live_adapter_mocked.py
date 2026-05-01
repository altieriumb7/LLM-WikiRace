import pytest
from wikirace.live_adapter import WikiRaceAdapter


def test_missing_base_url():
    with pytest.raises(RuntimeError):
        WikiRaceAdapter(base_url=None)
