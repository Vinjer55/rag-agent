import logging
import json

from src.services.search_service import search_documents
from src.services.generation_service import generate_answer_with_context, reformulate_query
from src.services.session_service import get_conversation_history, save_conversation_turn

logger = logging.getLogger(__name__)

def ask_question(query, session_id: str):
    logger.info(f"\nQuestion: {query}\n")
    
    # Get conversation history
    history = get_conversation_history(session_id)
    logger.info(f"Session {session_id}: Loaded {len(history)} messages")
    
    # Reformulate query if there's history
    search_query = query
    if history and needs_reformulation(query): # Only reformulate if really needed
        search_query = reformulate_query(query, history)
        logger.info(f"Reformulated query: {search_query}")
        
    
    # Search documents
    docs = search_documents(search_query, top_k=3)
    
    if not docs:
        yield "data: " + json.dumps({"type": "error", "content": "No relevant documents found"}) + "\n\n"
        return
    
    # Send sources first
    yield "data: " + json.dumps({
        "type": "sources",
        "content": [{"title": doc["title"], "source": doc["source"]} for doc in docs]
    }) + "\n\n"
    
    # Stream the answer
    full_answer = ""
    for chunk in generate_answer_with_context(query, docs, history):
        full_answer += chunk
        yield "data: " + json.dumps({"type": "content", "content": chunk}) + "\n\n"
    
    # Send completion signal
    yield "data: " + json.dumps({"type": "done"}) + "\n\n"
    
    # Save conversation
    save_conversation_turn(session_id, query, full_answer)
    
def needs_reformulation(query: str):
    standalone_indicators = ["what is", "define", "explain", "how to"]
    return not any(query.lower().startswith(ind) for ind in standalone_indicators)