from typing import List, Dict, Any
from app.core.llm_client import llm_completion
import json
from app.core.session_memory import SessionMemory

class PlannerAgent:
    def plan(self, user_query: str, session: SessionMemory) -> List[Dict[str, Any]]:
        prompt = (
            "You are a planning agent for a PDF Q&A system.\n"
            "Given the user question, decide among actions: RETRIEVE (with k), SEARCH_WEB, ANSWER, or ASK_CLARIFY. "
            "Choose the most appropriate sequence based on the question; do not assume local or web by default. "
            "Always return a list of actions in strict JSON (no extra text).\n\n"
            f"Conversation History (JSON array of turns): {session.history()}\n\n"
            "Examples:\n"
            "1) [{\"action\": \"RETRIEVE\", \"args\": {\"k\": 5}}, {\"action\": \"ANSWER\"}]\n"
            "2) [{\"action\": \"SEARCH_WEB\"}, {\"action\": \"ANSWER\"}]\n"
            "3) [{\"action\": \"ASK_CLARIFY\", \"args\": {\"question\": \"Please specify...\"}}]\n"
            f"Question: {user_query}\n"
        )
        result = llm_completion(prompt, model="mistralai/mixtral-8x7b-instruct", json_mode=True)
        try:
            plan = json.loads(result)
        except Exception:
            plan = [
                {"action": "RETRIEVE", "args": {"k": 5}},
                {"action": "ANSWER"}
            ]
        return plan
