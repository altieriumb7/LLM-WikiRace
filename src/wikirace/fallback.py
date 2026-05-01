from dataclasses import dataclass
from typing import Dict, List, Optional, Set


@dataclass
class FallbackResult:
    selected_page: Optional[str]
    fallback_reason: str
    terminal: bool = False


def select_fallback(current_page: str, outgoing_links: List[str], visited: Set[str], graph_metrics: Dict[str, Dict]) -> FallbackResult:
    unvisited = [p for p in outgoing_links if p not in visited]
    if not unvisited:
        return FallbackResult(None, "loop_exhausted", terminal=True)
    with_pr = [(p, graph_metrics.get(p, {}).get("pagerank")) for p in unvisited]
    available_pr = [x for x in with_pr if x[1] is not None]
    if available_pr:
        selected = sorted(available_pr, key=lambda x: x[1], reverse=True)[0][0]
        return FallbackResult(selected, "fallback_pagerank")
    with_deg = [(p, graph_metrics.get(p, {}).get("out_degree", 0) or 0) for p in unvisited]
    selected = sorted(with_deg, key=lambda x: x[1], reverse=True)[0][0]
    return FallbackResult(selected, "pagerank_unavailable")
