from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from app.core.graph import build_graph
from app.core.session_memory import SessionMemory
import logging

router = APIRouter()
logger = logging.getLogger("qa")

class AskRequest(BaseModel):
    session_id: str = Field(..., example="uuid")
    question: str

class AskResponse(BaseModel):
    answer: str
    sources: List[str]
    plan: List[Dict[str, Any]]

# Build graph once at module level
_graph = None

def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph

@router.post("/ask", response_model=AskResponse)
async def ask_endpoint(request: AskRequest):
    try:
        session_memory = SessionMemory(request.session_id)
        graph = get_graph()
        
        # Initialize state
        initial_state = {
            "question": request.question,
            "session_id": request.session_id,
            "plan": [],
            "contexts": [],
            "sources": [],
            "answer": "",
            "_needs_web_fallback": False,
            "_retrieval_empty": False
        }
        
        # Run the graph
        logger.info(f"Running graph for question: {request.question}")
        final_state = graph.invoke(initial_state)
        
        # Extract results
        answer = final_state.get("answer", "")
        sources = final_state.get("sources", [])
        plan = final_state.get("plan", [])
        
        # Ensure we have a plan (fallback to default if empty)
        if not plan:
            plan = [{"action": "RETRIEVE", "args": {"k": 5}}, {"action": "ANSWER"}]
        
        # Ensure we have an answer
        if not answer:
            answer = "I apologize, but I was unable to generate a response."
        
        # Save to session memory
        session_memory.save_turn(request.question, answer, sources)
        
        logger.info(f"Answer generated, sources: {sources}, plan: {plan}")
        return AskResponse(answer=answer, sources=sources, plan=plan)
    except Exception as e:
        logger.exception("QA endpoint error")
        raise HTTPException(status_code=500, detail=str(e))
