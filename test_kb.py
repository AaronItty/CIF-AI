import asyncio
import os
import sys

# Ensure the app root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dashboard.backend.db_client import SupabaseClient
from agent_core.embeddings import EmbeddingService
from agent_core.knowledge_base_service import KnowledgeBaseService

async def run_kb_test():
    try:
        print("====== KB TEST STARTED ======")
        print("1. Initializing DB client and Embedding service...")
        db_client = SupabaseClient()
        embed_service = EmbeddingService()
        kb_service = KnowledgeBaseService(db_client, embed_service)
        
        print("2. Getting Default Organization ID...")
        org_id = kb_service.get_default_org_id()
        print(f"Default Org ID: {org_id}")
        
        print("3. Ingesting test document...")
        test_text = "This is a dummy document about Telegram integration tests. Telegram is awesome for chatbots and allows fetching data from Supabase directly via the python handlers."
        test_bytes = test_text.encode('utf-8')
        doc_name = "test_telegram_doc.txt"
        
        doc_id = await kb_service.ingest_document(
            organization_id=org_id,
            name=doc_name,
            file_bytes=test_bytes
        )
        print(f"Ingested document ID: {doc_id}")
        
        print("4. Testing vector search...")
        query = "How to test Telegram chatbot integrations?"
        results = await kb_service.search_knowledge_base(
            organization_id=org_id,
            query=query,
            limit=2
        )
        
        print("Search Results:")
        print(results)
        
        print("5. Cleaning up test document...")
        kb_service.delete_document(doc_id)
        print("Cleaned up document from DB and Storage.")
        
        print("====== KB TEST PASSED ======")
    except Exception as e:
        print(f"====== KB TEST FAILED ======")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_kb_test())
