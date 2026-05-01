from wikirace.fallback import select_fallback

def test_escape_selects_hub_nonvisited():
    r=select_fallback('A',['B','C'],{'A','B'},{'C':{'pagerank':None,'out_degree':3}})
    assert r.selected_page=='C'
