from dataclasses import asdict, dataclass
from statistics import median
from typing import Dict, List, Optional


@dataclass
class AblationResult:
    run_id: str
    mode: str
    instance_id: str
    difficulty: str
    start_page: str
    target_page: str
    success: bool
    steps_used: int
    final_path: List[str]
    failure_reason: Optional[str]
    repeated_page_attempts: int = 0
    budget_rejections: int = 0
    schema_violations: int = 0
    trap_detections: int = 0
    strategic_replans: int = 0
    fallback_used: int = 0
    api_errors: int = 0


def summarize_mode(results: List[AblationResult]) -> Dict:
    succ = [r for r in results if r.success]
    ssteps = [r.steps_used for r in succ]
    return {
        "num_instances": len(results),
        "successes": len(succ),
        "failures": len(results) - len(succ),
        "success_rate": len(succ)/len(results) if results else 0,
        "average_steps_successful": (sum(ssteps)/len(ssteps)) if ssteps else None,
        "median_steps_successful": median(ssteps) if ssteps else None,
        "repeated_page_attempt_rate": (sum(r.repeated_page_attempts for r in results)/len(results)) if results else 0,
        "total_budget_rejections": sum(r.budget_rejections for r in results),
        "total_schema_violations": sum(r.schema_violations for r in results),
        "total_trap_detections": sum(r.trap_detections for r in results),
        "total_strategic_replans": sum(r.strategic_replans for r in results),
        "total_fallback_used": sum(r.fallback_used for r in results),
        "failure_reason_counts": {k: sum(1 for r in results if r.failure_reason==k) for k in sorted(set(r.failure_reason for r in results if r.failure_reason))}
    }
