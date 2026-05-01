from wikirace.results import AblationResult, summarize_mode

def test_schema_fields_and_summary():
    r=AblationResult('r','baseline','i','easy','A','T',False,30,['A'],'budget_exhausted')
    assert r.fallback_used==0
    s=summarize_mode([r])
    assert s['num_instances']==1 and s['failures']==1
