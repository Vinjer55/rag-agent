from src.services.search_service import search_documents
from src.services.generation_service import generate_answer

async def ask_question(query):
    """Complete RAG pipeline"""
    print(f"\nQuestion: {query}\n")
    
    # 1. Retrieve relevant documents
    docs = search_documents(query, top_k=3)
    
    print("Retrieved documents:")
    for i, doc in enumerate(docs, 1):
        print(f"{i}. {doc['title']} (score: {doc['@search.score']:.2f})")
    print()
    
    # 2. Generate answer
    answer = generate_answer(query, docs)
    
    print(f"Answer:\n{answer}\n")
    return answer