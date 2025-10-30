from typing import List, Dict, Any
from app.core.llm_client import llm_completion

class ReaderAgent:
    def synthesize(self, user_query: str, contexts: List[Dict[str, Any]]) -> str:
        context_text = "\n".join([c["content"] for c in contexts])
        prompt = (
            f"User Question: {user_query}\n"
            "Relevant Information:\n"
            f"{context_text}\n"
            "Answer clearly and cite supporting evidence from provided context."
        )
        return llm_completion(prompt)
