import asyncio
import os
import sys

# Ensure the app root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dashboard.backend.db_client import SupabaseClient
from agent_core.embeddings import EmbeddingService
from agent_core.knowledge_base_service import KnowledgeBaseService

async def main():
    log_file = "test_debug.log"
    with open(log_file, "w", encoding="utf-8") as f:
        try:
            f.write("Initializing...\n")
            db_client = SupabaseClient()
            embed_service = EmbeddingService()
            kb_service = KnowledgeBaseService(db_client, embed_service)
            
            org_id = kb_service.get_default_org_id()
            f.write(f"Org ID: {org_id}\n")
            
            doc_content = "SweetCrumbs is an online bakery. We delivery cookies. Price is Rs. 99."
            f.write("Ingesting...\n")
            
            doc_id = await kb_service.ingest_document(
                organization_id=org_id,
                name="debug.txt",
                file_bytes=doc_content.encode('utf-8')
            )
            f.write(f"Doc ID: {doc_id}\n")
            
            # Inspect table
            db_res = db_client.get_client().table("document_chunks").select("id, content, embedding").eq("document_id", doc_id).execute()
            f.write(f"DB Chunks Found: {len(db_res.data)}\n")
            if db_res.data:
                import numpy as np
                chunk = db_res.data[0]
                has_embedding = chunk.get("embedding") is not None
                f.write(f"Chunk 0 content: {chunk.get('content')}\n")
                f.write(f"Chunk 0 has embedding: {has_embedding}\n")
                if has_embedding:
                    # Log first few dims
                    f.write(f"Embedding snippet: {chunk['embedding'][:5]}...\n")
                    
                    # Local Similarity Check
                    query_vec = np.array(embed_service.embed_query("Where is the bakery?"), dtype=float)
                    
                    raw_emb = chunk.get("embedding")
                    if isinstance(raw_emb, str):
                        # Parse '[0.1, 0.2, ...]'
                        f.write("Note: Embedding returned as string, parsing...\n")
                        raw_emb = [float(x) for x in raw_emb.strip("[]").split(",")]
                    
                    chunk_vec = np.array(raw_emb, dtype=float)
                    
                    dot = np.dot(query_vec, chunk_vec)
                    norm_q = np.linalg.norm(query_vec)
                    norm_c = np.linalg.norm(chunk_vec)
                    sim = dot / (norm_q * norm_c)
                    f.write(f"LOCAL SIMILARITY: {sim:.4f}\n")

            f.write("Searching via RPC...\n")
            query = "Where is the bakery?"
            query_embedding = embed_service.embed_query(query)
            
            # Direct RPC call with error checking
            rpc_res = db_client.get_client().rpc("match_documents", {
                "query_embedding": query_embedding,
                "match_threshold": 0.0,
                "match_count": 1
            }).execute()
            
            f.write(f"RPC Response Data: {rpc_res.data}\n")
            if hasattr(rpc_res, 'error') and rpc_res.error:
                f.write(f"RPC Error: {rpc_res.error}\n")
            
            # Also try a raw select with similarity
            f.write("Trying raw SQL-like select...\n")
            raw_res = db_client.get_client().table("document_chunks").select("id, content").limit(1).execute()
            f.write(f"Raw select data: {raw_res.data}\n")
            
            f.write("Cleaning up...\n")
            kb_service.delete_document(doc_id)
            f.write("Done!\n")
            
        except Exception as e:
            f.write(f"ERROR: {e}\n")
            import traceback
            f.write(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())
