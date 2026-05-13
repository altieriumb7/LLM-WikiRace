from types import SimpleNamespace

import pytest

from wikirace.benchmark_adapter import BenchmarkStateAdapter, validate_batch_contract


def test_to_view_from_object_fields():
    adapter = BenchmarkStateAdapter()
    gs = SimpleNamespace(outgoing_links=["A", "B"], visited_pages=["X"], steps_used=3, target_page="T", current_page="C")
    view = adapter.to_view(gs)
    assert view.outgoing_links == ["A", "B"]
    assert view.visited_pages == ["X"]
    assert view.steps_used == 3
    assert view.target_page == "T"
    assert view.current_page == "C"


def test_to_view_from_dict_aliases():
    adapter = BenchmarkStateAdapter()
    view = adapter.to_view({"links": ["A"], "path": ["P1"], "step": "2"})
    assert view.outgoing_links == ["A"]
    assert view.visited_pages == ["P1"]
    assert view.steps_used == 2


def test_to_view_rejects_bad_schema():
    adapter = BenchmarkStateAdapter()
    with pytest.raises(ValueError):
        adapter.to_view({"links": "not-a-list"})


def test_validate_batch_contract():
    validate_batch_contract([0, 1], ["a", "b"], [{"output_tokens": 1}, {"output_tokens": 2}], [{}, {}])
    with pytest.raises(ValueError):
        validate_batch_contract([0], ["a", "b"], [{"output_tokens": 1}], [{}, {}])
