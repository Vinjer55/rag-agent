import os
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

# Initialize clients
openai_client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-01",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

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