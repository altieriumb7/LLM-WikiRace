from app import discover_configs, env_bool, get_runtime_settings


def test_demo_mode_default_disables_live(monkeypatch):
    monkeypatch.delenv("DEMO_MODE", raising=False)
    monkeypatch.delenv("ALLOW_LIVE_RUNS", raising=False)
    settings = get_runtime_settings()
    assert settings["demo_mode"] is True
    assert settings["allow_live_runs"] is False


def test_missing_openai_key_does_not_crash(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert get_runtime_settings()["openai_key_present"] is False


def test_env_bool_parsing(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "false")
    assert env_bool("DEMO_MODE", True) is False


def test_default_config_is_discoverable():
    configs = discover_configs("evals/config.yaml")
    assert "evals/config.yaml" in configs
