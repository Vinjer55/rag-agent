import os
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

openai_client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-01",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

def get_embedding(text):
    """Get embedding vector for text"""
    try:
        response = openai_client.embeddings.create(
            input=text,
            model=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"✗ Error generating embedding: {e}")
        raise