import uuid

from typing import Optional
from fastapi import APIRouter, HTTPException, Header
from src.services.query_service import ask_question
from src.models.query import QueryRequest

chat_router = APIRouter(tags=["Chat"])

@chat_router.post("/ask")
async def handle_question(request: QueryRequest, session_id: Optional[str] = Header(None, alias="X-Session-ID")):
    try:
        # Auto-generate session_id if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        result  = await ask_question(request.query, session_id)
        
        # Return session_id for client to reuse
        result["session_id"] = session_id
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal error occurred. {e}")