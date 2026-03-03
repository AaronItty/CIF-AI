import asyncio
import os
import sys

# Ensure the app root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dashboard.backend.db_client import SupabaseClient
from agent_core.embeddings import EmbeddingService
from agent_core.knowledge_base_service import KnowledgeBaseService

async def main():
    db_client = SupabaseClient()
    embed_service = EmbeddingService()
    kb_service = KnowledgeBaseService(db_client, embed_service)
    
    unique_str = "ZYX_UNIQUE_COOKIE_BREAD_123"
    print(f"Ingesting unique string: {unique_str}")
    
    org_id = kb_service.get_default_org_id()
    doc_id = await kb_service.ingest_document(
        organization_id=org_id,
        name="unique_test.txt",
        file_bytes=unique_str.encode('utf-8')
    )
    
    print(f"Verify presence via direct select...")
    res = db_client.get_client().table("document_chunks").select("id, content").ilike("content", f"%{unique_str}%").execute()
    print(f"Direct select results: {res.data}")
    
    if res.data:
        print("Data is PRESENT and ACCESSIBLE via Select.")
        print("Now trying RPC for this unique string...")
        rpc_res = db_client.get_client().rpc("match_documents", {
            "query_embedding": embed_service.embed_query(unique_str),
            "match_threshold": -1.0,
            "match_count": 5
        }).execute()
        print(f"RPC results: {rpc_res.data}")
    else:
        print("Data is NOT FOUND even via direct select!")

    kb_service.delete_document(doc_id)

if __name__ == "__main__":
    asyncio.run(main())
