from fastapi import FastAPI
from app.api import qa, memory

app = FastAPI(title="Chat With PDF Backend")

app.include_router(qa.router, prefix="/v1")
app.include_router(memory.router, prefix="/v1")

@app.get("/health")
def health():
    return {"status": "ok"}
