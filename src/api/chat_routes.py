import uuid
import json

from typing import Optional
from fastapi import APIRouter, HTTPException, Header
from src.services.query_service import ask_question
from src.models.query import QueryRequest
from fastapi.responses import StreamingResponse

chat_router = APIRouter(tags=["Chat"])

@chat_router.post("/ask")
async def handle_question(request: QueryRequest, session_id: Optional[str] = Header(None, alias="X-Session-ID")):
    try:
        # Auto-generate session_id if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        def event_generator():
            # Send session_id first
            yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"
            
            # Stream the response
            for chunk in ask_question(
                query=request.query,
                session_id=session_id
            ):
                yield chunk
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal error occurred. {e}")