from wikirace.experiments import mock_planner, mock_ranker


def test_mock_outputs_have_required_fields():
    ranked = mock_ranker({"outgoing_links": ["A"], "visited": []})
    c = ranked["candidates"][0]
    for k in ["page", "target_proximity", "hub_score", "estimated_dist", "milestone_progress", "novelty", "rationale", "combined_score"]:
        assert k in c
    plan = mock_planner({"target_page": "T"})
    for k in ["backbone", "current_milestone", "reasoning_summary", "escape_advice"]:
        assert k in plan
