from typing import Any, Dict, List
from .fallback import select_fallback
from .invariant_gate import GateConfig, InvariantGate
from .modes import ModeConfig
from .replan import evaluate_replan
from .state import initialize_state, transition_to, with_backbone, with_phase


class NavigatorConfig:
    def __init__(self, **kwargs):
        self.budget = int(kwargs.get("budget", 30))
        self.trap_target_score_threshold = int(kwargs.get("trap_target_score_threshold", 5))
        self.escape_resolved_outdegree_threshold = int(kwargs.get("escape_resolved_outdegree_threshold", 20))


class StratifiedNavigator:
    def __init__(self, adapter, tactical_model, strategic_model, cfg: NavigatorConfig):
        self.adapter = adapter
        self.tactical = tactical_model
        self.strategic = strategic_model
        self.cfg = cfg

    def run_game(self, instance, logger, mode: ModeConfig) -> Dict[str, Any]:
        state = initialize_state(instance.start_page, instance.target_page, self.cfg.budget)
        chat_history=[]
        counters={"repeated":0,"budget_rejections":0,"schema_violations":0,"trap":0,"replans":0,"fallback":0,"api_errors":0}
        gate = InvariantGate(GateConfig(budget=self.cfg.budget))
        while state.steps_used < state.budget:
            if self.adapter.is_target(state.current_page, state.target_page):
                return {"status":"success","state":state,**counters}
            try:
                links=self.adapter.get_outgoing_links(state.current_page)
                metrics=self.adapter.get_link_metrics(links)
            except Exception:
                counters["api_errors"]+=1
                return {"status":"failed","failure_reason":"api_error","state":state,**counters}

            if mode.baseline_chat_history:
                prompt={"current_page":state.current_page,"target_page":state.target_page,"steps_used":state.steps_used,"outgoing_links":links,"chat_history":chat_history}
                ranked=self.tactical.rank(prompt)
                if not ranked.get("candidates"):
                    counters["schema_violations"]+=1
                    return {"status":"failed","failure_reason":"invalid_model_move","state":state,**counters}
                nxt=ranked["candidates"][0]["page"]
                if nxt not in links:
                    return {"status":"failed","failure_reason":"invalid_model_move","state":state,**counters}
                if nxt in state.visited: counters["repeated"]+=1
                state=transition_to(state,nxt,float(ranked["candidates"][0].get("target_proximity",0)))
                chat_history.append({"from":state.path[-2],"to":nxt})
                continue

            ranked_resp=self.tactical.rank({"current_page":state.current_page,"target_page":state.target_page,"steps_used":state.steps_used,"budget":state.budget,"visited":list(state.visited),"phase":state.phase,"outgoing_links":links,"last_scores":list(state.last_scores),"strategic_backbone":list(state.backbone_plan or ()),"current_milestone":state.current_milestone})
            ranked=ranked_resp.get("candidates",[])
            if ranked_resp.get("failure_reason"): counters["schema_violations"]+=1

            if mode.trap_detection or mode.decay_replan or mode.periodic_replan:
                decision=evaluate_replan(state.steps_used,state.budget,list(state.last_scores),len(links),ranked,self.cfg.trap_target_score_threshold)
                if mode.trap_detection and decision.should_escape and mode.escape_logic:
                    counters["trap"]+=1; logger({"event_type":"trap_detected"}); state=with_phase(state,"escape");
                if mode.use_backbone_planning and mode.periodic_replan and decision.reason=="periodic" and mode.strategic_model:
                    plan=self.strategic.plan({"current_page":state.current_page,"target_page":state.target_page,"steps_used":state.steps_used,"budget":state.budget,"visited":list(state.visited),"outgoing_links":links})
                    counters["replans"]+=1; state=with_backbone(state,plan.get("backbone",[]),plan.get("current_milestone",""))
                if mode.use_backbone_planning and mode.decay_replan and decision.reason=="decay" and mode.strategic_model:
                    plan=self.strategic.plan({"current_page":state.current_page,"target_page":state.target_page,"steps_used":state.steps_used,"budget":state.budget,"visited":list(state.visited),"outgoing_links":links})
                    counters["replans"]+=1; state=with_backbone(state,plan.get("backbone",[]),plan.get("current_milestone",""))

            if state.phase=="escape" and mode.escape_logic:
                fb=select_fallback(state.current_page,links,set(state.visited),{k:v.__dict__ for k,v in metrics.items()})
                if fb.terminal: return {"status":"failed","failure_reason":"loop_exhausted","state":state,**counters}
                counters["fallback"]+=1
                state=transition_to(state,fb.selected_page,0.0,phase="progress")
                logger({"event_type":"escape_move"})
                continue

            choice=None
            if mode.use_gate:
                # basic invariants by config
                filtered=[]
                for c in ranked[:mode.top_k]:
                    ok=True
                    if "acyclicity" in mode.enabled_invariants and c["page"] in state.visited: counters["repeated"]+=1; ok=False
                    if "budget" in mode.enabled_invariants and state.steps_used+1+int(c.get("estimated_dist",30))>state.budget: counters["budget_rejections"]+=1; ok=False
                    if ok: filtered.append(c)
                if filtered: choice=filtered[0]
            else:
                choice=ranked[0] if ranked else None

            if not choice:
                if mode.deterministic_fallback:
                    fb=select_fallback(state.current_page,links,set(state.visited),{k:v.__dict__ for k,v in metrics.items()})
                    if fb.terminal: return {"status":"failed","failure_reason":"loop_exhausted","state":state,**counters}
                    counters["fallback"]+=1
                    choice={"page":fb.selected_page,"target_proximity":0}
                else:
                    return {"status":"failed","failure_reason":"invalid_model_move","state":state,**counters}
            state=transition_to(state,choice["page"],float(choice.get("target_proximity",0)))

        return {"status":"failed","failure_reason":"budget_exhausted","state":state,**counters}
