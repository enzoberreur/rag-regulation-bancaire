"""
Document upload and management endpoints.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
import os
from datetime import datetime
import uuid

from app.core.database import get_db
from app.core.config import settings
from app.models.document import Document
from app.services.document_processor import DocumentProcessor

router = APIRouter()


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a document and process it for RAG.
    
    Args:
        file: The file to upload (PDF, DOCX, TXT)
        db: Database session
    """
    # Validate file type
    allowed_extensions = {".pdf", ".docx", ".doc", ".txt"}
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file_ext} not allowed. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # All documents are treated the same way
    document_type = "document"
    
    # Create storage directory if it doesn't exist
    os.makedirs(settings.storage_path, exist_ok=True)
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_path = os.path.join(settings.storage_path, f"{file_id}{file_ext}")
    
    # Save file
    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
    
    # Create document record
    doc = Document(
        id=uuid.uuid4(),
        name=file.filename,
        file_path=file_path,
        file_size=len(content),
        file_type=file_ext[1:],  # Remove the dot
        document_type=document_type,
        uploaded_at=datetime.utcnow(),
    )
    
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    # Process document (chunking and embedding) asynchronously
    try:
        processor = DocumentProcessor(db)
        await processor.process_document(doc.id)
    except Exception as e:
        # If processing fails, we still keep the document record
        # but mark it as unprocessed
        doc.document_metadata = {"processing_error": str(e), "processed": False}
        db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Document uploaded but processing failed: {str(e)}"
        )
    
    return JSONResponse(
        status_code=201,
        content={
            "id": str(doc.id),
            "name": doc.name,
            "size": doc.file_size,
            "type": doc.document_type,
            "uploaded_at": doc.uploaded_at.isoformat(),
        }
    )


@router.get("/")
async def list_documents(
    db: Session = Depends(get_db),
):
    """
    List all uploaded documents.
    
    Args:
        db: Database session
    """
    documents = db.query(Document).order_by(Document.uploaded_at.desc()).all()
    
    return [
        {
            "id": str(doc.id),
            "name": doc.name,
            "size": doc.file_size,
            "type": doc.document_type,
            "uploaded_at": doc.uploaded_at.isoformat(),
        }
        for doc in documents
    ]


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
):
    """
    Delete a document and all its chunks.
    
    Args:
        document_id: UUID of the document to delete
        db: Database session
    """
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")
    
    doc = db.query(Document).filter(Document.id == doc_uuid).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete file from storage
    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception as e:
            # Log error but continue with DB deletion
            print(f"Error deleting file {doc.file_path}: {e}")
    
    # Delete document (chunks will be cascade deleted)
    db.delete(doc)
    db.commit()
    
    return {"message": "Document deleted successfully"}

