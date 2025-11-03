from typing import List, Dict, Any
from app.core.llm_client import llm_completion
import json
from app.core.session_memory import SessionMemory
from datetime import datetime, timezone

class PlannerAgent:
    def plan(self, user_query: str, session: SessionMemory) -> List[Dict[str, Any]]:
        now_iso = datetime.now(timezone.utc).astimezone().isoformat()
        prompt = (
            "You are a planning agent for a PDF Q&A system.\n"
            "Available actions: RETRIEVE (with k), SEARCH_WEB, ANSWER, ASK_CLARIFY.\n"
            "Decision policy (not hard-coded, but your own reasoning):\n"
            "- Prefer RETRIEVE when the answer is likely within the provided PDFs.\n"
            "- Prefer SEARCH_WEB when the question appears to require up-to-date, time-sensitive, or external information beyond the PDFs. Base this entirely on your own judgment from the question and conversation, not on any fixed keywords.\n"
            "- Your world knowledge may be out of date; when recency could matter or you are uncertain, choose SEARCH_WEB before ANSWER.\n"
            "- Use ASK_CLARIFY only if the question is genuinely ambiguous.\n"
            "- Always end with ANSWER after gathering context.\n"
            "Return only a JSON list of actions (no extra text).\n\n"
            f"Current Datetime: {now_iso}\n"
            f"Conversation History (JSON array of turns): {session.history()}\n\n"
            "Examples (illustrative, not exhaustive):\n"
            "1) Q: How do LLMs generate SQL from text?\n   Plan: [{\"action\": \"RETRIEVE\", \"args\": {\"k\": 5}}, {\"action\": \"ANSWER\"}]\n"
            "2) Q: What is the latest LLM news as of today?\n   Plan: [{\"action\": \"SEARCH_WEB\"}, {\"action\": \"ANSWER\"}]\n"
            "3) Q: Compare methods A and B mentioned in the PDFs.\n   Plan: [{\"action\": \"RETRIEVE\", \"args\": {\"k\": 5}}, {\"action\": \"ANSWER\"}]\n"
            "4) Q: Tell me more.\n   Plan: [{\"action\": \"ASK_CLARIFY\", \"args\": {\"question\": \"Please specify the topic.\"}}]\n\n"
            f"Question: {user_query}\n"
        )
        result = llm_completion(prompt)
        try:
            plan = json.loads(result)
        except Exception:
            plan = [
                {"action": "RETRIEVE", "args": {"k": 5}},
                {"action": "ANSWER"}
            ]
        return plan
