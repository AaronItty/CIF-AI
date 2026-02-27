"""
Dashboard API Endpoints.
Provides backend-ready endpoints for the frontend application.
"""

# Example: Using FastAPI or Flask patterns

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/kb", tags=["Knowledge Base"])

class DocumentResponse(BaseModel):
    id: str
    name: str
    status: str
    chunk_count: int
    created_at: str

class DashboardRoutes:
    def __init__(self, kb_service: 'KnowledgeBaseService'):
        self.kb_service = kb_service

    def register_routes(self, app):
        @router.get("/files", response_model=List[DocumentResponse])
        async def get_files():
            org_id = self.kb_service.get_default_org_id()
            res = self.kb_service.get_documents(org_id)
            return res.data

        @router.post("/upload")
        async def upload_file(file: UploadFile = File(...)):
            org_id = self.kb_service.get_default_org_id()
            content = await file.read()
            text_content = content.decode("utf-8", errors="ignore")
            
            try:
                doc_id = await self.kb_service.ingest_document(org_id, file.filename, text_content)
                return {"id": doc_id, "status": "processing"}
            except Exception as e:
                print(f"API ERROR in /upload: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @router.delete("/files/{file_id}")
        async def delete_file(file_id: str):
            self.kb_service.delete_document(file_id)
            return {"status": "deleted"}

        app.include_router(router)

