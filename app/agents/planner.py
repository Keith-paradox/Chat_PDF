from typing import List, Dict, Any
from app.core.llm_client import llm_completion
import json

class PlannerAgent:
    def plan(self, user_query: str, session) -> List[Dict[str, Any]]:
        prompt = (
            "You are a planning agent for a PDF Q&A system.\n"
            "Given the user question, prefer answering from the local PDF chunks via RETRIEVE first, then ANSWER. "
            "Only use SEARCH_WEB if the question is clearly about current events or explicitly requires external information. "
            "Avoid ASK_CLARIFY unless the question is truly ambiguous. "
            "Always return a list of actions in JSON.\n\n"
            "Example (preferred): [{\"action\": \"RETRIEVE\", \"args\": {\"k\": 5}}, {\"action\": \"ANSWER\"}]\n"
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

        # Safety: ensure we always retrieve then answer as a baseline
        actions = [step["action"] for step in plan if isinstance(step, dict) and "action" in step]
        if "RETRIEVE" not in actions:
            plan.insert(0, {"action": "RETRIEVE", "args": {"k": 5}})
        if "ANSWER" not in actions:
            plan.append({"action": "ANSWER"})
        return plan
