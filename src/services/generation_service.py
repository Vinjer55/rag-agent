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

def generate_answer_with_context(
    query: str, 
    docs: list, 
    history: list
):
    
    # Build context from documents
    doc_context = "\n\n".join([
        f"Document: {doc['title']}\n{doc['content']}" 
        for doc in docs
    ])
    
    # Build messages with history
    messages = [
        {
            "role": "system",
            "content": f"""You are a helpful assistant. Answer questions based on the provided context.

            Context from documents:
            {doc_context}

            Always cite sources and maintain conversation context."""
        }
    ]
    
    # Add conversation history (last 5 turns to keep it manageable)
    recent_history = history[-10:] if len(history) > 10 else history
    messages.extend(recent_history)
    
    # Add current question
    messages.append({
        "role": "user",
        "content": query
    })
    
    response = openai_client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        messages=messages,
        temperature=0.3,
        max_tokens=800,
        stream=True
    )
    
    # Yield chunks as they arrive with safety checks
    for chunk in response:
        if chunk.choices and len(chunk.choices) > 0:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content
                
def reformulate_query(current_query: str, history: list):
    # Build context from last 3 turns
    recent_context = history[-6:] if len(history) > 6 else history
    context_text = "\n".join([
        f"{msg['role']}: {msg['content']}" 
        for msg in recent_context
    ])
    
    prompt = f"""Given this conversation:
        {context_text}

        The user now asks: "{current_query}"

        If this is a follow-up question, rewrite it as a standalone question with full context.
        If it's already standalone, return it as-is.

        Standalone question:"""

    response = openai_client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=100
    )
    
    reformulated = response.choices[0].message.content.strip()
    return reformulated