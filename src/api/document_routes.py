import os

from fastapi import BackgroundTasks, UploadFile
from fastapi import APIRouter, HTTPException
from src.services.document_service import process_and_ingest

document_router = APIRouter(tags=["Document"])

@document_router.post("/ingest")
async def ingest_document_endpoint(file: UploadFile, background_tasks: BackgroundTasks):
    # Ensure temp directory exists
    os.makedirs("./temp", exist_ok=True)
    
    # Save file first
    file_path = f"./temp/{file.filename}"
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Process in background
    background_tasks.add_task(process_and_ingest, file_path, file.filename)
    
    return {
        "status": "processing",
        "message": f"{file.filename} is being processed"
    }