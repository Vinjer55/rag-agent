import logging

from src.services.search_service import search_documents
from src.services.generation_service import generate_answer_with_context, reformulate_query
from src.services.session_service import get_conversation_history, save_conversation_turn

logger = logging.getLogger(__name__)

async def ask_question(query, session_id: str):
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
        answer = "I couldn't find relevant information in the documents."
        save_conversation_turn(session_id, query, answer)
        return {
            "answer": answer,
            "sources": [],
            "reformulated_query": search_query if history else None
        }
    
    logger.info("Retrieved documents:")
    for i, doc in enumerate(docs, 1):
        logger.info(f"{i}. {doc['title']} (score: {doc['@search.score']:.2f})")
    
    # Generate answer with conversation context
    answer = generate_answer_with_context(
        query=query,
        docs=docs,
        history=history
    )
    
    # Save this turn to conversation history
    save_conversation_turn(session_id, query, answer)
    
    return {
        "answer": answer,
        "sources": docs,
        "reformulated_query": search_query if history else None
    }
    
def needs_reformulation(query: str):
    standalone_indicators = ["what is", "define", "explain", "how to"]
    return not any(query.lower().startswith(ind) for ind in standalone_indicators)