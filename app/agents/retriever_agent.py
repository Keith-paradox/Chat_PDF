from typing import List, Dict, Any
from app.core.vectorstore import get_vectorstore
from app.core.embeddings import embed_text

class RetrieverAgent:
    def retrieve(self, query: str, k: int = 5, history: List[Dict[str, Any]] | None = None) -> List[Dict[str, Any]]:
        vs = get_vectorstore()
        # Augment the query with the last turn(s) for coreference (e.g., "it", "they")
        augmented_query = query
        if history:
            last_turns = history[-2:]  # use up to last 2 turns
            prior = []
            for t in last_turns:
                q = t.get("question")
                a = t.get("answer")
                if q:
                    prior.append(f"Q: {q}")
                if a:
                    prior.append(f"A: {a}")
            if prior:
                augmented_query = "\n".join(prior) + "\nCurrent: " + query
        embedding = embed_text(augmented_query)
        results = vs.similarity_search(embedding, k)
        return results  # List of {"content", "metadata"}
