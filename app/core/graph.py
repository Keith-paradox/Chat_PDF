from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

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
    state["plan"] = plan
    return state


def node_retrieve(state: GraphState) -> GraphState:
    retriever = RetrieverAgent()
    k = 5
    for step in state.get("plan", []):
        if step.get("action") == "RETRIEVE":
            k = step.get("args", {}).get("k", 5)
            break
    results = retriever.retrieve(state["question"], k=k)
    state.setdefault("contexts", [])
    state.setdefault("sources", [])
    state["contexts"].extend(results)
    state["sources"].extend([c["metadata"]["source"] for c in results])
    return state


def node_search_web(state: GraphState) -> GraphState:
    web = WebSearchAgent()
    snippet = web.search(state["question"])  # string
    state.setdefault("contexts", [])
    state.setdefault("sources", [])
    state["contexts"].append({"content": snippet, "metadata": {"source": "web"}})
    state["sources"].append("web")
    return state


def node_reader(state: GraphState) -> GraphState:
    reader = ReaderAgent()
    session = SessionMemory(state["session_id"])
    history = session.history()
    answer = reader.synthesize(state["question"], state.get("contexts", []), history)
    state["answer"] = answer
    return state


def route_edges(state: GraphState) -> str:
    # Drive edges based on the plan computed by the planner
    plan: List[Dict[str, Any]] = state.get("plan", [])
    if not plan:
        return "reader"
    # Consume the next action
    next_action = plan.pop(0)
    state["plan"] = plan
    action = next_action.get("action")
    if action == "RETRIEVE":
        return "retrieve"
    if action == "SEARCH_WEB":
        return "search_web"
    if action == "ANSWER":
        return "reader"
    if action == "ASK_CLARIFY":
        # No active clarification loop; proceed to reader with existing context
        return "reader"
    return "reader"


def build_graph() -> StateGraph:
    graph = StateGraph(GraphState)
    graph.add_node("planner", node_planner)
    graph.add_node("retrieve", node_retrieve)
    graph.add_node("search_web", node_search_web)
    graph.add_node("reader", node_reader)

    # Start at planner, then branch based on plan until reader, then END
    graph.set_entry_point("planner")
    graph.add_conditional_edges("planner", route_edges, {"retrieve": "retrieve", "search_web": "search_web", "reader": "reader"})
    graph.add_conditional_edges("retrieve", route_edges, {"retrieve": "retrieve", "search_web": "search_web", "reader": "reader"})
    graph.add_conditional_edges("search_web", route_edges, {"retrieve": "retrieve", "search_web": "search_web", "reader": "reader"})
    graph.add_edge("reader", END)

    # In-memory checkpointing per session_id to carry state if extended
    memory = MemorySaver()
    app = graph.compile(checkpointer=memory)
    return app


