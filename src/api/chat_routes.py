from fastapi import APIRouter, HTTPException
from query import ask_question

chat_router = APIRouter(tags=["Chat"])

@chat_router.post("/ask")
async def question(query: str):
    try:
        answer = await ask_question(query)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal error occurred. {e}")