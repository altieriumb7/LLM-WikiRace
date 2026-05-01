from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional
import json

class ConfigValidationError(ValueError): ...

@dataclass(frozen=True)
class ModeConfig:
    strategy: Literal['baseline','state_only','stratified','full']
    model: Optional[str]=None
    tactical_model: Optional[str]=None
    strategic_model: Optional[str]=None
    budget: int=30
    top_k: int=5
    beam_width: int=1
    replan_interval: int=5
    decay_replan: bool=False
    escape_threshold: Optional[int]=None
    deterministic_fallback: bool=False
    oracle_db_path: Optional[str]=None

    def __post_init__(self):
        s=self.strategy
        if s in ('baseline','state_only'):
            if not self.model: raise ConfigValidationError(f'{s} requires model')
            if self.strategic_model is not None: raise ConfigValidationError(f'{s} must not set strategic_model')
        if s in ('stratified','full') and (not self.tactical_model or not self.strategic_model):
            raise ConfigValidationError(f'{s} requires tactical_model and strategic_model')
        if s=='baseline':
            if self.escape_threshold is not None: raise ConfigValidationError('baseline must not set escape_threshold')
            if self.deterministic_fallback: raise ConfigValidationError('baseline must not enable deterministic_fallback')
            if self.oracle_db_path is not None: raise ConfigValidationError('baseline must not set oracle_db_path')
        if s!='full' and self.escape_threshold is not None: raise ConfigValidationError('escape_threshold is only valid for full strategy')
        if not (1 <= self.budget <= 30): raise ConfigValidationError('budget must be in 1..30')
        if self.top_k < 1: raise ConfigValidationError('top_k must be >= 1')
        if self.beam_width < 1: raise ConfigValidationError('beam_width must be >= 1')


def _parse_yaml(path: Path) -> dict:
    data={}
    for ln in path.read_text().splitlines():
        s=ln.strip()
        if not s or s.startswith('#') or ':' not in s: continue
        k,v=s.split(':',1); v=v.strip()
        if v in ('null','None'): val=None
        elif v in ('true','false'): val=(v=='true')
        elif v.isdigit(): val=int(v)
        elif v.startswith('['): val=json.loads(v.replace("'",'"'))
        else: val=v.strip('"')
        data[k.strip()]=val
    return data

def load_mode(path: Path) -> ModeConfig:
    return ModeConfig(**_parse_yaml(path))
