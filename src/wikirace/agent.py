from .state import GameState
from .results import Result

def run_game(start:str,target:str,strategy,adapter,budget:int=30):
    state=GameState(start,target,0,budget,(start,),frozenset({start}))
    counters={"repeated_page_attempts":0,"budget_rejections":0,"schema_violations":0,"trap_detections":0,"strategic_replans":0,"fallback_used":0,"api_errors":0}
    while state.steps_used<budget:
        if adapter.is_target(state.current_page,target):
            return Result(True,state.steps_used,state.path,**counters)
        try: candidates=adapter.get_outgoing_links(state.current_page)
        except Exception:
            counters['api_errors']+=1; return Result(False,state.steps_used,state.path,'api_error',**counters)
        if not candidates:
            return Result(False,state.steps_used,state.path,'dead_end',**counters)
        move,meta=strategy.select_move(state,candidates)
        for k in counters: counters[k]+=int(meta.get(k,0))
        if move is None: return Result(False,state.steps_used,state.path,meta.get('failure_reason','invalid_model_move'),**counters)
        if move in state.visited: counters['repeated_page_attempts']+=1
        state=state.next(move)
    return Result(False,state.steps_used,state.path,'budget_exhausted',**counters)
