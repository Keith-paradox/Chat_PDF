from typing import List, Dict, Any
from app.core.llm_client import llm_completion
from datetime import datetime, timezone

class ReaderAgent:
    def synthesize(self, user_query: str, contexts: List[Dict[str, Any]], history: List[Dict[str, Any]] | None = None) -> str:
        history_text = "\n".join(
            [f"Q: {h.get('question')}\nA: {h.get('answer')}" for h in (history or [])]
        )
        context_text = "\n".join([c["content"] for c in contexts])
        now_iso = datetime.now(timezone.utc).astimezone().isoformat()
        prompt = (
            f"You are a knowledgeable assistant. Use ONLY the provided context (from local PDFs and/or web snippets) to answer.\n"
            f"If web snippets are present, treat them as the most recent source for time-sensitive questions and cite them.\n"
            f"Prefer quoting or paraphrasing web snippets including dates and URLs when available. Do not claim you cannot browse or lack information.\n"
            f"You MUST provide a helpful answer based on the provided context, even if it's partial or from web sources only.\n\n"
            f"Current Datetime: {now_iso}\n\n"
            f"Conversation History (may be empty):\n{history_text}\n\n"
            f"User Question: {user_query}\n"
            "Context:\n"
            f"{context_text}\n\n"
            "Answer:"
        )
        return llm_completion(prompt)
