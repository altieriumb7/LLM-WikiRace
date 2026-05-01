import pytest
from wikirace.config import ModeConfig, ConfigValidationError

def test_invalid_configs():
    with pytest.raises(ConfigValidationError): ModeConfig(strategy='baseline',model='x',deterministic_fallback=True)
    with pytest.raises(ConfigValidationError): ModeConfig(strategy='baseline',model='x',escape_threshold=1)
    with pytest.raises(ConfigValidationError): ModeConfig(strategy='state_only')
    with pytest.raises(ConfigValidationError): ModeConfig(strategy='state_only',model='x',strategic_model='y')
    with pytest.raises(ConfigValidationError): ModeConfig(strategy='stratified',tactical_model='x')
    with pytest.raises(ConfigValidationError): ModeConfig(strategy='full',strategic_model='x')
    with pytest.raises(ConfigValidationError): ModeConfig(strategy='state_only',model='x',beam_width=0)
    with pytest.raises(ConfigValidationError): ModeConfig(strategy='state_only',model='x',top_k=0)
    with pytest.raises(ConfigValidationError): ModeConfig(strategy='state_only',model='x',budget=999)


def test_oracle_config_rules(tmp_path):
    db=str(tmp_path/'x.sqlite')
    with pytest.raises(ConfigValidationError): ModeConfig(strategy='baseline',model='x',oracle_db_path=db)
    ModeConfig(strategy='full',tactical_model='x',strategic_model='y',escape_threshold=10,deterministic_fallback=True,oracle_db_path=db)
    ModeConfig(strategy='full',tactical_model='x',strategic_model='y',escape_threshold=10,deterministic_fallback=True)
    ModeConfig(strategy='baseline',model='x')
