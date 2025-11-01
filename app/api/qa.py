from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import json
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

        # Normalize plan to a list[dict] with action/args
        normalized_plan = []
        if isinstance(plan, dict):
            plan = [plan]
        for step in plan or []:
            if isinstance(step, dict):
                if "action" in step:
                    normalized_plan.append(step)
            elif isinstance(step, str):
                try:
                    obj = json.loads(step)
                    if isinstance(obj, dict) and "action" in obj:
                        normalized_plan.append(obj)
                except Exception:
                    continue
        plan = normalized_plan

        retrieved_chunks = []
        sources = []
        answer = ""
        for step in plan:
            if step["action"] == "RETRIEVE":
                retrieved_chunks = retriever.retrieve(
                    request.question,
                    k=step.get("args", {}).get("k", 5),
                    history=session_memory.history(),
                )
                sources = [c["metadata"]["source"] for c in retrieved_chunks]
            elif step["action"] == "SEARCH_WEB":
                web_context = web_search.search(request.question)
                retrieved_chunks.append({"content": web_context, "metadata": {"source": "web"}})
                # Track source explicitly so the response indicates origin
                if "web" not in sources:
                    sources.append("web")
            elif step["action"] == "ANSWER":
                answer = reader.synthesize(request.question, retrieved_chunks, session_memory.history())
            elif step["action"] == "ASK_CLARIFY":
                # Defer setting a clarification answer; try to synthesize first in fallback
                pass

        # Fallbacks to ensure an answer, preferring web if local PDF retrieval yielded nothing
        if not answer:
            if not retrieved_chunks:
                # Try local retrieval with history-aware query
                try:
                    retrieved_chunks = retriever.retrieve(request.question, k=5, history=session_memory.history())
                    sources = [c["metadata"]["source"] for c in retrieved_chunks]
                except Exception:
                    retrieved_chunks = []
            if not retrieved_chunks:
                # Fall back to web search if PDFs didn't yield usable context
                web_context = web_search.search(request.question)
                retrieved_chunks.append({"content": web_context, "metadata": {"source": "web"}})
                if "web" not in sources:
                    sources.append("web")
            # Synthesize from whatever context we have
            answer = reader.synthesize(request.question, retrieved_chunks, session_memory.history())
        
        # Final check: if answer indicates lack of info and we haven't searched web yet, do it now
        if answer and any(phrase in answer.lower() for phrase in ["cannot", "don't have", "does not contain", "sorry", "unable to", "no information", "not provided"]) and "web" not in sources:
            logger.info("Answer indicates lack of information, attempting web search")
            try:
                web_context = web_search.search(request.question)
                retrieved_chunks = [{"content": web_context, "metadata": {"source": "web"}}]
                sources = ["web"]
                answer = reader.synthesize(request.question, retrieved_chunks, session_memory.history())
                # Update plan to reflect web search was used
                plan = [{"action": "RETRIEVE", "args": {"k": 5}}, {"action": "SEARCH_WEB"}, {"action": "ANSWER"}]
            except Exception as e:
                logger.exception("Web search fallback failed")
        
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
