from sentence_transformers import SentenceTransformer
import threading

_lock = threading.Lock()
_model = None

def get_model():
    global _model
    with _lock:
        if _model is None:
            _model = SentenceTransformer("all-MiniLM-L6-v2")
        return _model

def embed_text(text: str):
    model = get_model()
    return model.encode([text])[0]
