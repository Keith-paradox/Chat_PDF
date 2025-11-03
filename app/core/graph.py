from typing import Dict, Any, List
from langgraph.graph import StateGraph, END

from app.agents.planner import PlannerAgent
from app.agents.retriever_agent import RetrieverAgent
from app.agents.reader_agent import ReaderAgent
from app.agents.web_search_agent import WebSearchAgent
from app.core.session_memory import SessionMemory


# Graph state schema
class GraphState(dict):
    # keys: question, session_id, history, plan, contexts, sources, answer
    pass


def node_planner(state: GraphState) -> GraphState:
    session = SessionMemory(state["session_id"])
    planner = PlannerAgent()
    plan = planner.plan(state["question"], session)
    
    # Normalize plan to ensure it's a list of dicts
    normalized_plan = []
    if isinstance(plan, dict):
        plan = [plan]
    if isinstance(plan, list):
        for step in plan:
            if isinstance(step, dict) and "action" in step:
                normalized_plan.append(step)
    
    # Fallback to default plan if empty
    if not normalized_plan:
        normalized_plan = [
            {"action": "RETRIEVE", "args": {"k": 5}},
            {"action": "ANSWER"}
        ]
    
    state["plan"] = normalized_plan
    return state


def node_retrieve(state: GraphState) -> GraphState:
    retriever = RetrieverAgent()
    session = SessionMemory(state["session_id"])
    k = 5
    # Find RETRIEVE action in plan to get k value
    plan_copy = list(state.get("plan", []))
    for step in plan_copy:
        if step.get("action") == "RETRIEVE":
            k = step.get("args", {}).get("k", 5)
            break
    results = retriever.retrieve(state["question"], k=k, history=session.history())
    state.setdefault("contexts", [])
    state.setdefault("sources", [])
    
    # If no results, mark as empty (will route to web search in normal flow)
    if not results:
        state["_retrieval_empty"] = True
    else:
        state["contexts"].extend(results)
        state["sources"].extend([c["metadata"]["source"] for c in results])
        state["_retrieval_empty"] = False
    
    return state


def node_search_web(state: GraphState) -> GraphState:
    web = WebSearchAgent()
    snippet = web.search(state["question"])  # string
    state.setdefault("contexts", [])
    state.setdefault("sources", [])
    state["contexts"].append({"content": snippet, "metadata": {"source": "web"}})
    state["sources"].append("web")
    # Clear retrieval_empty flag since we now have web context
    state["_retrieval_empty"] = False
    return state


def node_reader(state: GraphState) -> GraphState:
    reader = ReaderAgent()
    session = SessionMemory(state["session_id"])
    history = session.history()
    contexts = state.get("contexts", [])
    
    # If no contexts and no answer yet, ensure we have something
    if not contexts and not state.get("answer"):
        # This should not happen if graph is correct, but safety check
        return state
    
    answer = reader.synthesize(state["question"], contexts, history)
    state["answer"] = answer
    
    # Check if answer indicates lack of info and web wasn't used - trigger web fallback
    if answer and any(phrase in answer.lower() for phrase in ["cannot", "don't have", "does not contain", "sorry", "unable to", "no information", "not provided"]) and "web" not in state.get("sources", []):
        # Set a flag to trigger web search
        state["_needs_web_fallback"] = True
    else:
        state["_needs_web_fallback"] = False
    
    return state


def node_web_fallback(state: GraphState) -> GraphState:
    """Fallback web search when answer indicates lack of information"""
    web = WebSearchAgent()
    snippet = web.search(state["question"])
    state.setdefault("contexts", [])
    state.setdefault("sources", [])
    state["contexts"] = [{"content": snippet, "metadata": {"source": "web"}}]
    state["sources"] = ["web"]
    # Clear the fallback flags to prevent loops
    state["_needs_web_fallback"] = False
    state["_retrieval_empty"] = False
    return state


def route_edges(state: GraphState) -> str:
    # Check for web fallback first
    if state.get("_needs_web_fallback"):
        return "web_fallback"
    
    # Drive edges based on the plan computed by the planner
    plan: List[Dict[str, Any]] = state.get("plan", [])
    if not plan:
        return "reader"
    # Get next action without consuming it yet (we'll check if we should)
    if plan:
        next_action = plan[0]
        action = next_action.get("action")
        if action == "RETRIEVE":
            plan.pop(0)  # Consume it
            state["plan"] = plan
            return "retrieve"
        elif action == "SEARCH_WEB":
            plan.pop(0)
            state["plan"] = plan
            return "search_web"
        elif action == "ANSWER":
            plan.pop(0)
            state["plan"] = plan
            return "reader"
        elif action == "ASK_CLARIFY":
            plan.pop(0)
            state["plan"] = plan
            return "reader"
    return "reader"


def route_after_retrieve(state: GraphState) -> str:
    """Route after retrieve - check if retrieval was empty, then check plan"""
    # If retrieval returned nothing, go to web search
    if state.get("_retrieval_empty"):
        return "search_web"
    # Otherwise continue with plan
    return route_edges(state)


def route_after_web(state: GraphState) -> str:
    """Route after web search - check plan or fallback"""
    if state.get("_needs_web_fallback"):
        return "web_fallback"
    return route_edges(state)


def route_after_reader(state: GraphState) -> str:
    """Route after reader - check if web fallback needed, otherwise end"""
    if state.get("_needs_web_fallback"):
        return "web_fallback"
    return "__end__"


def route_after_web_fallback(state: GraphState) -> str:
    """After web fallback, go to reader to synthesize, then end"""
    return "reader"


def build_graph():
    graph = StateGraph(dict)  # Use plain dict instead of GraphState to avoid typing issues
    graph.add_node("planner", node_planner)
    graph.add_node("retrieve", node_retrieve)
    graph.add_node("search_web", node_search_web)
    graph.add_node("reader", node_reader)
    graph.add_node("web_fallback", node_web_fallback)

    # Start at planner
    graph.set_entry_point("planner")
    
    # Planner routes based on plan
    graph.add_conditional_edges("planner", route_edges, {
        "retrieve": "retrieve",
        "search_web": "search_web",
        "reader": "reader",
        "web_fallback": "web_fallback"
    })
    
    # After retrieve, continue with plan or web fallback
    graph.add_conditional_edges("retrieve", route_after_retrieve, {
        "retrieve": "retrieve",
        "search_web": "search_web",
        "reader": "reader",
        "web_fallback": "web_fallback"
    })
    
    # After web search, continue with plan or web fallback
    graph.add_conditional_edges("search_web", route_after_web, {
        "retrieve": "retrieve",
        "search_web": "search_web",
        "reader": "reader",
        "web_fallback": "web_fallback"
    })
    
    # After reader, check if fallback needed or end
    graph.add_conditional_edges("reader", route_after_reader, {
        "web_fallback": "web_fallback",
        "__end__": END
    })
    
    # After web fallback, synthesize final answer
    graph.add_conditional_edges("web_fallback", route_after_web_fallback, {
        "reader": "reader"
    })

    app = graph.compile()
    return app


