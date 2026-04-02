import os

from dotenv import load_dotenv
from src.services.embedding_service import get_embedding
from azure.search.documents.models import VectorizedQuery
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

load_dotenv()

search_client = SearchClient(
    endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    index_name="documents-index",
    credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_KEY"))
)

def search_documents(query, top_k=3):
    """Hybrid search: vector + keyword"""
    query_vector = get_embedding(query)
    
    vector_query = VectorizedQuery(
        vector=query_vector,
        k_nearest_neighbors=top_k,
        fields="content_vector"
    )
    
    # Enable semantic ranking in search
    results = search_client.search(
        search_text=query,
        vector_queries=[vector_query],
        query_type="semantic",
        semantic_configuration_name="my-semantic-config",
        top=3
    )
    
    return list(results)