from typing import List, Dict, Any
from app.core.vectorstore import get_vectorstore
from app.core.embeddings import embed_text

class RetrieverAgent:
    def retrieve(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        vs = get_vectorstore()
        embedding = embed_text(query)
        results = vs.similarity_search(embedding, k)
        return results  # List of {"content", "metadata"}
