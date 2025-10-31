from typing import List, Dict, Any
from app.core.llm_client import llm_completion

class ReaderAgent:
    def synthesize(self, user_query: str, contexts: List[Dict[str, Any]], history: List[Dict[str, Any]] | None = None) -> str:
        history_text = "\n".join(
            [f"Q: {h.get('question')}\nA: {h.get('answer')}" for h in (history or [])]
        )
        context_text = "\n".join([c["content"] for c in contexts])
        prompt = (
            f"You are a knowledgeable assistant. Use ONLY the provided context (from local PDFs and/or web snippets) to answer.\n"
            f"If web snippets are present, you DO have that information; do not claim inability to browse.\n"
            f"Cite specific phrases from the context when possible.\n\n"
            f"Conversation History (may be empty):\n{history_text}\n\n"
            f"User Question: {user_query}\n"
            "Context:\n"
            f"{context_text}\n\n"
            "Answer:"
        )
        return llm_completion(prompt)
