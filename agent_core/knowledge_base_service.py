from typing import List
import uuid
import re
import io
from datetime import datetime
from pypdf import PdfReader
from agent_core.embeddings import EmbeddingService
from dashboard.db_client import SupabaseClient

class KnowledgeBaseService:
    def __init__(self, db_client: SupabaseClient, embedding_service: EmbeddingService):
        self.db = db_client.get_client()
        self.embeddings = embedding_service

    def chunk_text(self, text: str, chunk_size: int = 150, overlap: int = 30) -> List[str]:
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

    def clean_text(self, text: str) -> str:
        """
        Removes null characters and hidden control characters.
        """
        text = text.replace("\x00", "")
        # Remove control characters [\x00-\x1f\x7f]
        text = re.sub(r"[\x00-\x1f\x7f]", "", text)
        return text.strip()

    def get_default_org_id(self) -> str:
        """Fetch the first organization or create a default one if none exist."""
        res = self.db.table("organizations").select("id").limit(1).execute()
        if res.data:
            return res.data[0]["id"]
        
        # Auto-create a default organization for the prototype/demo
        print("DEBUG: No organizations found. Creating 'Default Organization'...")
        res = self.db.table("organizations").insert({
            "name": "Default Organization",
            "business_description": "Initial organization for the AI platform."
        }).execute()
        
        if res.data:
            return res.data[0]["id"]
            
        raise Exception("Failed to create or find an organization in the database.")

    async def ingest_document(self, organization_id: str, name: str, file_bytes: bytes, document_id: str = None):
        """
        Full ingestion pipeline: Upload to Storage -> Save doc -> Extract -> Chunk -> Embed -> Store Chunks.
        """
        # 1. Upload file to Supabase Storage
        file_path = f"org_{organization_id}/{uuid.uuid4()}_{name}"
        try:
            print(f"DEBUG: Uploading {name} to storage...")
            self.db.storage.from_("knowledge-base").upload(
                path=file_path,
                file=file_bytes,
                file_options={"content-type": "application/pdf" if name.lower().endswith(".pdf") else "text/plain"}
            )
        except Exception as e:
            print(f"DEBUG STORAGE ERROR: {str(e)}")

        file_size = len(file_bytes)
        mime_type = "application/pdf" if name.lower().endswith(".pdf") else "text/plain"

        if not document_id:
            # 2. Create document record with storage_path
            res = self.db.table("documents").insert({
                "organization_id": organization_id,
                "name": name,
                "storage_path": file_path,
                "mime_type": mime_type,
                "file_size_bytes": file_size,
                "status": "processing"
            }).execute()
            document_id = res.data[0]["id"]
        else:
            self.db.table("documents").update({
                "status": "processing",
                "storage_path": file_path,
                "mime_type": mime_type,
                "file_size_bytes": file_size
            }).eq("id", document_id).execute()

        try:
            # 3. Extract text from bytes
            if name.lower().endswith(".pdf"):
                print(f"DEBUG: Extracting text from PDF...")
                pdf = PdfReader(io.BytesIO(file_bytes))
                content = ""
                for page in pdf.pages:
                    content += page.extract_text() + "\n"
            else:
                content = file_bytes.decode("utf-8", errors="ignore")

            # 4. Clean and Chunk
            # PostgreSQL does not support null characters or certain control chars in text fields
            content = self.clean_text(content)
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

    def get_document_by_id(self, document_id: str):
        return self.db.table("documents").select("*").eq("id", document_id).single().execute()

    def get_kb_stats(self, organization_id: str):
        """Returns aggregated metrics for the KB."""
        res = self.db.table("documents").select("chunk_count, uploaded_at").eq("organization_id", organization_id).execute()
        docs = res.data or []
        
        total_docs = len(docs)
        total_chunks = sum(d["chunk_count"] or 0 for d in docs)
        avg_chunks = total_chunks / total_docs if total_docs > 0 else 0
        last_updated = max((d["uploaded_at"] for d in docs if d["uploaded_at"]), default=None)

        return {
            "total_documents": total_docs,
            "total_chunks": total_chunks,
            "avg_chunks_per_doc": round(avg_chunks, 1),
            "last_updated": last_updated
        }

    async def search_knowledge_base(self, organization_id: str, query: str, limit: int = 5):
        """Performs vector search to retrieve relevant chunks."""
        print(f"DEBUG: Searching KB for: {query}")
        # nomic-embed-text-v1.5 requires 'search_query: ' prefix for queries
        query_embedding = self.embeddings.embed_query(query)
        
        # Use the RPC 'match_documents' we defined in SQL
        res = self.db.rpc("match_documents", {
            "query_embedding": query_embedding,
            "match_threshold": 0.0, # Temporarily 0.0 for testing
            "match_count": limit
        }).execute()
        
        print("VECTOR SEARCH RESULTS:", res.data)
        
        if not res.data:
            return {
                "message": "No relevant knowledge found.",
                "results": []
            }
            
        return {
            "message": f"Found {len(res.data)} matching results.",
            "results": res.data
        }

    def delete_document(self, document_id: str):
        """
        Deletes the document record, its chunks (via cascade), and its physical file from storage.
        """
        # 1. Get the document to find storage_path
        res = self.db.table("documents").select("storage_path").eq("id", document_id).single().execute()
        if res.data:
            storage_path = res.data.get("storage_path")
            if storage_path:
                try:
                    # 2. Delete from Storage
                    print(f"DEBUG: Deleting {storage_path} from storage...")
                    # .remove() expects a list of paths
                    self.db.storage.from_("knowledge-base").remove([storage_path])
                except Exception as e:
                    print(f"DEBUG STORAGE DELETE ERROR: {str(e)}")

        # 3. Delete from Database (cascading deletes handle chunks)
        return self.db.table("documents").delete().eq("id", document_id).execute()
