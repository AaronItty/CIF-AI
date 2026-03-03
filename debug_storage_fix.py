import asyncio
import os
import sys
from dashboard.backend.db_client import SupabaseClient
from agent_core.embeddings import EmbeddingService
from agent_core.knowledge_base_service import KnowledgeBaseService

async def debug_storage():
    db_client = SupabaseClient()
    embed_service = EmbeddingService()
    kb_service = KnowledgeBaseService(db_client, embed_service)
    
    # Get latest doc
    res = db_client.get_client().table('documents').select('id, name, storage_path').order('uploaded_at', desc=True).limit(1).execute()
    if not res.data:
        print("No documents found")
        return
        
    doc = res.data[0]
    print(f"Testing Doc: {doc['name']} ({doc['id']})")
    print(f"Path: {doc['storage_path']}")
    
    try:
        signed = db_client.get_client().storage.from_('knowledge-base').create_signed_url(
            path=doc['storage_path'],
            expires_in=3600
        )
        print(f"Result Type: {type(signed)}")
        print(f"Result: {signed}")
        
        url = None
        if isinstance(signed, dict):
            url = signed.get("signedURL") or signed.get("signedUrl")
        elif isinstance(signed, str):
            url = signed
        elif hasattr(signed, 'signed_url'):
             url = signed.signed_url
             
        print(f"Extracted URL: {url}")
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(debug_storage())
