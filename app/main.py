from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from app.api import qa, memory, upload

app = FastAPI(title="Chat With PDF Backend")

app.include_router(qa.router, prefix="/v1")
app.include_router(memory.router, prefix="/v1")
app.include_router(upload.router, prefix="/v1")

@app.get("/health")
def health():
    return {"status": "ok"}

# Middleware to disable caching for static files
class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.url.path.endswith(('.css', '.js', '.html')):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

app.add_middleware(NoCacheMiddleware)

# Serve static UI
app.mount("/", StaticFiles(directory="app/ui", html=True), name="ui")