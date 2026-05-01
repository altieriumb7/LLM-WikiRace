from dataclasses import dataclass, asdict
from typing import Optional, Tuple

@dataclass
class Result:
    success: bool
    steps_used: int
    path: Tuple[str, ...]
    failure_reason: Optional[str] = None
    repeated_page_attempts: int = 0
    budget_rejections: int = 0
    schema_violations: int = 0
    trap_detections: int = 0
    strategic_replans: int = 0
    fallback_used: int = 0
    api_errors: int = 0

    def to_dict(self):
        d = asdict(self)
        d['path'] = list(self.path)
        return d
