from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.core.session_memory import SessionMemory

router = APIRouter()

class ClearRequest(BaseModel):
    session_id: str

@router.post("/clear_memory")
async def clear_memory_endpoint(request: ClearRequest):
    try:
        session = SessionMemory(request.session_id)
        session.clear()
        return {"status": "cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_history(session_id: str = Query(...)):
    try:
        session = SessionMemory(session_id)
        return {"session_id": session_id, "history": session.history()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
