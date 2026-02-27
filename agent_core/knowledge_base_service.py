from typing import List
import uuid
from datetime import datetime
from agent_core.embeddings import EmbeddingService
from dashboard.db_client import SupabaseClient

class KnowledgeBaseService:
    def __init__(self, db_client: SupabaseClient, embedding_service: EmbeddingService):
        self.db = db_client.get_client()
        self.embeddings = embedding_service

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Simple sliding window chunking.
        """
        chunks = []
        words = text.split()
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)
            if i + chunk_size >= len(words):
                break
        return chunks

    async def ingest_document(self, organization_id: str, name: str, content: str, document_id: str = None):
        """
        Full ingestion pipeline: Save doc -> Chunk -> Embed -> Store Chunks.
        """
        if not document_id:
            # Create document record if not exists
            res = self.db.table("documents").insert({
                "organization_id": organization_id,
                "name": name,
                "storage_path": "", # Placeholder to avoid NOT NULL constraints
                "status": "processing"
            }).execute()
            document_id = res.data[0]["id"]
        else:
            self.db.table("documents").update({"status": "processing"}).eq("id", document_id).execute()

        try:
            chunks = self.chunk_text(content)
            print(f"DEBUG: Chunked into {len(chunks)} parts")
            
            for i, chunk in enumerate(chunks):
                print(f"DEBUG: Embedding chunk {i}...")
                embedding = self.embeddings.embed_document(chunk)
                
                print(f"DEBUG: Inserting chunk {i} to DB...")
                self.db.table("document_chunks").insert({
                    "organization_id": organization_id,
                    "document_id": document_id,
                    "chunk_index": i,
                    "content": chunk,
                    "embedding": embedding
                }).execute()

            # Mark as ready
            self.db.table("documents").update({
                "status": "ready",
                "chunk_count": len(chunks),
                "processed_at": datetime.utcnow().isoformat()
            }).eq("id", document_id).execute()
            print("DEBUG: Ingestion successful")
            
            return document_id

        except Exception as e:
            print(f"DEBUG INGESTION ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            self.db.table("documents").update({
                "status": "failed",
                "last_error": str(e)
            }).eq("id", document_id).execute()
            raise e

    def get_documents(self, organization_id: str):
        return self.db.table("documents").select("*").eq("organization_id", organization_id).order("created_at", desc=True).execute()

    def delete_document(self, document_id: str):
        # Cascading deletes will handle document_chunks
        return self.db.table("documents").delete().eq("id", document_id).execute()
