from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from typing import List
import os
import logging
from app.ingest.ingest_pdfs import ingest
from app.config import settings
from app.core.vectorstore import get_vectorstore

router = APIRouter()
logger = logging.getLogger("upload")

# Ensure pdfs directory exists
PDFS_DIR = "/app/pdfs"
os.makedirs(PDFS_DIR, exist_ok=True)

@router.post("/upload")
async def upload_pdf(files: List[UploadFile] = File(...)):
    """
    Upload one or more PDF files and automatically ingest them into the vector store.
    """
    results = []
    total_chunks = 0
    
    for file in files:
        try:
            # Validate file type
            if not file.filename.lower().endswith('.pdf'):
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": "Only PDF files are allowed"
                })
                continue
            
            # Save uploaded file
            file_path = os.path.join(PDFS_DIR, file.filename)
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            # Ingest the PDF
            try:
                doc_id = os.path.splitext(file.filename)[0]
                chunks = ingest(file_path, doc_id=doc_id)
                total_chunks += chunks
                
                results.append({
                    "filename": file.filename,
                    "doc_id": doc_id,
                    "chunks_ingested": chunks,
                    "status": "success",
                    "message": f"Successfully ingested {chunks} chunks"
                })
            except Exception as ingest_error:
                logger.exception("Ingestion error")
                # Clean up uploaded file if ingestion fails
                if os.path.exists(file_path):
                    os.remove(file_path)
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": f"Failed to ingest: {str(ingest_error)}"
                })
        except Exception as e:
            logger.exception("Upload error")
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": str(e)
            })
    
    # Return summary
    success_count = sum(1 for r in results if r.get("status") == "success")
    error_count = len(results) - success_count
    
    return JSONResponse({
        "status": "completed",
        "results": results,
        "summary": {
            "total_files": len(results),
            "successful": success_count,
            "failed": error_count,
            "total_chunks_ingested": total_chunks
        }
    })

@router.post("/clear_vectorstore")
async def clear_vectorstore():
    """
    Clear all ingested documents from ChromaDB vector store.
    """
    try:
        vs = get_vectorstore()
        deleted_count = vs.clear_all()
        return JSONResponse({
            "status": "success",
            "deleted_chunks": deleted_count,
            "message": f"Successfully cleared {deleted_count} chunks from vector store"
        })
    except Exception as e:
        logger.exception("Clear vectorstore error")
        raise HTTPException(status_code=500, detail=str(e))

