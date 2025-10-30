from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from app.agents.planner import PlannerAgent
from app.agents.retriever_agent import RetrieverAgent
from app.agents.reader_agent import ReaderAgent
from app.agents.web_search_agent import WebSearchAgent
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

@router.post("/ask", response_model=AskResponse)
async def ask_endpoint(request: AskRequest):
    try:
        session_memory = SessionMemory(request.session_id)
        planner = PlannerAgent()
        retriever = RetrieverAgent()
        reader = ReaderAgent()
        web_search = WebSearchAgent()

        plan = planner.plan(request.question, session_memory)
        logger.info(f"Plan: {plan}")

        retrieved_chunks = []
        sources = []
        answer = ""
        for step in plan:
            if step["action"] == "RETRIEVE":
                retrieved_chunks = retriever.retrieve(request.question, k=step["args"].get("k", 5))
                sources = [c["metadata"]["source"] for c in retrieved_chunks]
            elif step["action"] == "SEARCH_WEB":
                web_context = web_search.search(request.question)
                retrieved_chunks.append({"content": web_context, "metadata": {"source": "web"}})
            elif step["action"] == "ANSWER":
                answer = reader.synthesize(request.question, retrieved_chunks)
            elif step["action"] == "ASK_CLARIFY":
                # Defer setting a clarification answer; try to synthesize first in fallback
                pass

        # Fallback to ensure we return an answer
        if not answer:
            if not retrieved_chunks:
                try:
                    retrieved_chunks = retriever.retrieve(request.question, k=5)
                    sources = [c["metadata"]["source"] for c in retrieved_chunks]
                except Exception:
                    retrieved_chunks = []
            if retrieved_chunks:
                answer = reader.synthesize(request.question, retrieved_chunks)
            else:
                answer = "Please clarify your question for more accurate answers."
        session_memory.save_turn(request.question, answer, sources)
        return AskResponse(answer=answer, sources=sources, plan=plan)
    except Exception as e:
        logger.exception("QA endpoint error")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug/retrieve")
async def debug_retrieve(q: str, k: int = 5):
    try:
        retriever = RetrieverAgent()
        results = retriever.retrieve(q, k)
        return {
            "num_results": len(results),
            "sources": [r["metadata"]["source"] for r in results],
            "previews": [r["content"][:200] for r in results],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
