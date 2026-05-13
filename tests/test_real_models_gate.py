import pytest

from wikirace.config import ModeConfig
from wikirace.strategies import build_strategy


def test_real_models_require_openai_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        build_strategy(ModeConfig(strategy="state_only", model="gpt-test"), object(), use_real_models=True)
