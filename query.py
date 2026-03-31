import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from openai import AzureOpenAI

load_dotenv()

# Initialize clients
openai_client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-01",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

search_client = SearchClient(
    endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    index_name="documents-index",
    credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_KEY"))
)

def get_embedding(text):
    response = openai_client.embeddings.create(
        input=text,
        model=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
    )
    return response.data[0].embedding

def search_documents(query, top_k=3):
    """Hybrid search: vector + keyword"""
    query_vector = get_embedding(query)
    
    vector_query = VectorizedQuery(
        vector=query_vector,
        k_nearest_neighbors=top_k,
        fields="content_vector"
    )
    
    results = search_client.search(
        search_text=query,
        vector_queries=[vector_query],
        select=["content", "title", "source"],
        top=top_k
    )
    
    return list(results)

def generate_answer(query, context_docs):
    """Generate answer using GPT-4"""
    context = "\n\n".join([
        f"Source: {doc['title']}\n{doc['content']}" 
        for doc in context_docs
    ])
    
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that answers questions based on the provided context. Always cite your sources."
        },
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
        }
    ]
    
    response = openai_client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        messages=messages,
        temperature=0.3,
        max_tokens=800
    )
    
    return response.choices[0].message.content

def ask_question(query):
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

# Usage
if __name__ == "__main__":
    ask_question("What are the main topics covered in the documents?")