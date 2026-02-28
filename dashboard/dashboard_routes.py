"""
Dashboard API Endpoints.
Provides backend-ready endpoints for the frontend application.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/api/kb", tags=["Knowledge Base"])

class DocumentResponse(BaseModel):
    id: str
    name: str
    status: str
    chunk_count: int
    file_size_bytes: Optional[int]
    mime_type: Optional[str]
    uploaded_at: str
    processed_at: Optional[str]
    last_error: Optional[str]
    storage_path: Optional[str]

class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 5

# --- Global Reference for dependecy access ---
_kb_service: Optional['KnowledgeBaseService'] = None

class DashboardRoutes:
    def __init__(self, kb_service: 'KnowledgeBaseService'):
        global _kb_service
        _kb_service = kb_service

    def register_routes(self, app):
        app.include_router(router)

# --- Route Implementations ---

@router.get("/files", response_model=List[DocumentResponse])
async def get_files():
    if not _kb_service:
        raise HTTPException(status_code=500, detail="KB Service not initialized")
    org_id = _kb_service.get_default_org_id()
    res = _kb_service.get_documents(org_id)
    return res.data

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not _kb_service:
        raise HTTPException(status_code=500, detail="KB Service not initialized")
    org_id = _kb_service.get_default_org_id()
    content = await file.read()
    try:
        doc_id = await _kb_service.ingest_document(org_id, file.filename, content)
        return {"id": doc_id, "status": "processing"}
    except Exception as e:
        print(f"API ERROR in /upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_stats():
    if not _kb_service:
        raise HTTPException(status_code=500, detail="KB Service not initialized")
    org_id = _kb_service.get_default_org_id()
    return _kb_service.get_kb_stats(org_id)

@router.post("/search")
async def search_kb(req: SearchRequest):
    if not _kb_service:
        raise HTTPException(status_code=500, detail="KB Service not initialized")
    org_id = _kb_service.get_default_org_id()
    return await _kb_service.search_knowledge_base(org_id, req.query, req.limit)

@router.get("/view/{file_id}")
async def view_file(file_id: str):
    if not _kb_service:
        raise HTTPException(status_code=500, detail="KB Service not initialized")
    res = _kb_service.get_document_by_id(file_id)
    if not res.data:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc = res.data
    if not doc.get("storage_path"):
        raise HTTPException(status_code=400, detail="Document has no storage path")

    try:
        signed = _kb_service.db.storage.from_("knowledge-base").create_signed_url(
            path=doc["storage_path"],
            expires_in=60
        )
        print("SIGNED DEBUG:", signed)

        # Handle different response structures
        url = None
        if isinstance(signed, dict):
            url = signed.get("signedURL") or signed.get("signedUrl")
        elif isinstance(signed, str):
            url = signed

        if not url:
            raise Exception(f"Could not extract signed URL from response: {signed}")

        return {"url": url}
    except Exception as e:
        print(f"SIGNED URL ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/files/{file_id}")
async def delete_file(file_id: str):
    if not _kb_service:
        raise HTTPException(status_code=500, detail="KB Service not initialized")
    _kb_service.delete_document(file_id)
    return {"status": "deleted"}
