import chromadb
from chromadb.config import Settings as ChromaSettings
import os
from app.config import settings

def get_vectorstore():
    client = chromadb.PersistentClient(path=settings.chroma_dir)
    collection = client.get_or_create_collection("pdf_chunks")
    return VectorStore(collection)

class VectorStore:
    def __init__(self, collection):
        self.collection = collection

    def similarity_search(self, embedding, k=5):
        # Ensure embedding is a plain Python list for Chroma
        if hasattr(embedding, "tolist"):
            embedding = embedding.tolist()
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=k,
            include=["documents", "metadatas"]
        )
        docs = []
        for text, meta in zip(results['documents'][0], results['metadatas'][0]):
            docs.append({"content": text, "metadata": meta})
        return docs

    def add_chunks(self, contents, embeddings, metadatas):
        # Generate stable IDs for each chunk using metadata
        ids = [
            f"{m.get('source','unknown')}::p{m.get('page','?')}::c{m.get('chunk','?')}"
            for m in metadatas
        ]
        self.collection.upsert(
            ids=ids,
            documents=contents,
            embeddings=embeddings,
            metadatas=metadatas
        )
    
    def clear_all(self):
        """Delete all chunks from the collection."""
        # Get all IDs and delete them
        results = self.collection.get()
        if results['ids']:
            self.collection.delete(ids=results['ids'])
        return len(results['ids']) if results['ids'] else 0
