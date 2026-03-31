import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
    SemanticConfiguration,
    SemanticSearch,
    SemanticPrioritizedFields,
    SemanticField,
    SearchField,
    SearchFieldDataType
)
from openai import AzureOpenAI

load_dotenv()

# Initialize clients
openai_client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-01",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

search_credential = AzureKeyCredential(os.getenv("AZURE_SEARCH_KEY"))
index_client = SearchIndexClient(
    endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    credential=search_credential
)

# Define index schema
def create_search_index(index_name="documents-index"):
    """Create search index with vector and semantic search capabilities"""
    
    # Define fields
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="content", type=SearchFieldDataType.String),
        SearchableField(name="title", type=SearchFieldDataType.String),
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=1536,
            vector_search_profile_name="myHnswProfile"
        ),
        SimpleField(name="source", type=SearchFieldDataType.String, filterable=True),
    ]
    
    # Configure vector search
    vector_search = VectorSearch(
        profiles=[VectorSearchProfile(
            name="myHnswProfile",
            algorithm_configuration_name="myHnsw"
        )],
        algorithms=[HnswAlgorithmConfiguration(name="myHnsw")]
    )
    
    # Configure semantic search (FIXED for new API version)
    semantic_search = SemanticSearch(
        configurations=[
            SemanticConfiguration(
                name="my-semantic-config",
                prioritized_fields=SemanticPrioritizedFields(
                    content_fields=[SemanticField(field_name="content")]
                )
            )
        ]
    )
    
    # Create index
    index = SearchIndex(
        name=index_name,
        fields=fields,
        vector_search=vector_search,
        semantic_search=semantic_search
    )
    
    try:
        result = index_client.create_or_update_index(index)
        print(f"✓ Index '{index_name}' created successfully")
        return index_name
    except Exception as e:
        print(f"✗ Error creating index: {e}")
        raise
 
# Chunk documents
def chunk_text(text, chunk_size=1000, overlap=200):
    """Simple chunking strategy with overlap"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    return chunks
 
# Generate embeddings
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
 
# Ingest document
def ingest_document(file_path, index_name="documents-index"):
    """Process and index a document"""
    
    print(f"\n📄 Processing: {file_path}")
    
    # Read document
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"✗ Error reading file: {e}")
        return
    
    # Chunk content
    chunks = chunk_text(content)
    print(f"📊 Created {len(chunks)} chunks")
    
    # Prepare documents for indexing
    search_client = SearchClient(
        endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        index_name=index_name,
        credential=search_credential
    )
    
    documents = []
    for i, chunk in enumerate(chunks):
        print(f"  Processing chunk {i+1}/{len(chunks)}...", end='\r')
        
        try:
            embedding = get_embedding(chunk)
            doc = {
                "id": f"{os.path.basename(file_path).replace('.', '_')}_{i}",
                "content": chunk,
                "title": os.path.basename(file_path),
                "content_vector": embedding,
                "source": file_path
            }
            documents.append(doc)
        except Exception as e:
            print(f"\n✗ Error processing chunk {i}: {e}")
            continue
    
    # Upload to index
    try:
        result = search_client.upload_documents(documents)
        successful = sum(1 for r in result if r.succeeded)
        print(f"\n✓ Successfully uploaded {successful}/{len(documents)} chunks from {file_path}")
        return result
    except Exception as e:
        print(f"\n✗ Error uploading documents: {e}")
        raise
 
# Usage
if __name__ == "__main__":
    print("=" * 60)
    print("Azure AI Search - Document Ingestion")
    print("=" * 60)
    
    # Create index
    try:
        index_name = create_search_index()
    except Exception as e:
        print(f"\nFailed to create index. Please check your configuration.")
        exit(1)
    
    # Ingest a document
    # Replace with your actual document path
    sample_file = "sample_document.txt"
    
    if os.path.exists(sample_file):
        ingest_document(sample_file, index_name)
    else:
        print(f"\n⚠ Sample file '{sample_file}' not found.")
        print(f"Please create a sample document or specify an existing file path.")
        print(f"\nExample usage:")
        print(f"  ingest_document('path/to/your/document.txt', '{index_name}')")