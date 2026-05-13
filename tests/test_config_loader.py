from pathlib import Path

import pytest

from wikirace.config import ConfigValidationError, load_mode


def test_load_mode_uses_real_yaml():
    cfg = load_mode(Path("configs/modes/full.yaml"))
    assert cfg.strategy == "full"
    assert cfg.deterministic_fallback is True


def test_nested_config_is_not_a_mode_config():
    with pytest.raises(ConfigValidationError):
        load_mode(Path("configs/stratified_navigator.yaml"))
