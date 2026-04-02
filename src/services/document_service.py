import os
import logging
import re

from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.storage.blob import BlobServiceClient
from ingest import chunk_text, get_embedding

logger = logging.getLogger(__name__)

load_dotenv()

search_client = SearchClient(
    endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    index_name="documents-index",
    credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_KEY"))
)

blob_service_client  = BlobServiceClient.from_connection_string(os.getenv("AZURE_STORAGE_CONNECTION_STRING"))
container_client = blob_service_client.get_container_client("documents")

def process_and_ingest(file_path, filename):
    # Check if already ingested
    if is_document_ingested(filename):
        logger.info(f"{filename} already exists, skipping")
        os.remove(file_path)  # Clean up temp file
        return {"status": "already_exists"}
    
    try:
        # Upload to Blob Storage first
        with open(file_path, 'rb') as data:
            blob_client = container_client.get_blob_client(filename)
            blob_client.upload_blob(data, overwrite=True)
            blob_url = blob_client.url
            logger.info(f"Uploaded to blob storage: {blob_url}")
        
        # Read file content for processing
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
    except Exception as e:
        logger.error(f"Error reading/uploading file: {e}")
        os.remove(file_path)  # Clean up
        return {"status": "error", "message": str(e)}
    
    # Chunk the content
    chunks = chunk_text(content)
    logger.info(f"Created {len(chunks)} chunks")
    
    # Generate embeddings and prepare documents
    documents = []
    for i, chunk in enumerate(chunks):
        logger.info(f"Processing chunk {i+1}/{len(chunks)}")
        try:
            embedding = get_embedding(chunk)
            doc = {
                "id": f"{sanitize_filename(filename)}_{i}", 
                "content": chunk,
                "title": filename,
                "content_vector": embedding,
                "source": blob_url  # Store blob URL instead of local path
            }
            documents.append(doc)
        except Exception as e:
            logger.error(f"Error processing chunk {i}: {e}")
            continue
    
    # Upload to Azure AI Search
    try:
        result = search_client.upload_documents(documents)
        successful = sum(1 for r in result if r.succeeded)
        logger.info(f"✓ Successfully uploaded {successful}/{len(documents)} chunks")
        
        # Clean up temp file
        os.remove(file_path)
        
        return {
            "status": "success",
            "chunks_indexed": successful,
            "blob_url": blob_url
        }
        
    except Exception as e:
        logger.error(f"Error uploading to search index: {e}")
        # Clean up temp file even on error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise
    
def is_document_ingested(filename):
    results = search_client.search(
        search_text="*",
        filter=f"source eq '{filename}'",
        top=1
    )
    return any(results)

def sanitize_filename(filename):
    """Convert filename to valid Azure Search key"""
    name = os.path.splitext(filename)[0]  # Remove extension
    name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)  # Replace invalid chars
    return name