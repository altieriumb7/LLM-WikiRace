from wikirace.experiments import load_config, run_instances


def test_mock_graph_find_path():
    cfg = load_config("configs/stratified_navigator.yaml")
    rows = run_instances([{"start_page": "Backpropagation", "target_page": "Photosynthesis"}], cfg, "full_stratified")
    assert rows[0]["success"]
