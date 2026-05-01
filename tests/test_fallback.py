from wikirace.fallback import select_fallback


def test_pr_first():
    r=select_fallback('A',['B','C'],{'A'},{'B':{'pagerank':0.1,'out_degree':2},'C':{'pagerank':0.9,'out_degree':1}})
    assert r.selected_page=='C'

def test_degree_when_no_pr():
    r=select_fallback('A',['B','C'],{'A'},{'B':{'pagerank':None,'out_degree':2},'C':{'pagerank':None,'out_degree':9}})
    assert r.selected_page=='C' and r.fallback_reason=='pagerank_unavailable'

def test_loop_exhausted():
    r=select_fallback('A',['B'],{'A','B'},{})
    assert r.terminal and r.fallback_reason=='loop_exhausted'
