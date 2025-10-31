from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api import qa, memory

app = FastAPI(title="Chat With PDF Backend")

app.include_router(qa.router, prefix="/v1")
app.include_router(memory.router, prefix="/v1")

@app.get("/health")
def health():
    return {"status": "ok"}

# Serve static UI
app.mount("/", StaticFiles(directory="app/ui", html=True), name="ui")