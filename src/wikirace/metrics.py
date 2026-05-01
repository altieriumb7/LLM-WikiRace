from statistics import median
from typing import Any, Dict, List


def summarize(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    successes = [r for r in results if r.get("success")]
    steps = [r["steps"] for r in successes]
    return {
        "success_rate": len(successes) / len(results) if results else 0,
        "average_steps_successful": sum(steps) / len(steps) if steps else None,
        "median_steps_successful": median(steps) if steps else None,
        "budget_rejection_count": sum(r.get("metrics", {}).get("budget_rejections", 0) for r in results),
        "trap_detection_count": sum(r.get("metrics", {}).get("trap_detections", 0) for r in results),
        "strategic_replan_count": sum(r.get("metrics", {}).get("strategic_replans", 0) for r in results),
    }
