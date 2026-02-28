import asyncio
from dashboard.db_client import SupabaseClient
from agent_core.embeddings import EmbeddingService
from agent_core.knowledge_base_service import KnowledgeBaseService

async def main():
    try:
        db = SupabaseClient()
        embed = EmbeddingService()
        kb = KnowledgeBaseService(db, embed)
        res = await kb.ingest_document("00000000-0000-0000-0000-000000000000", "test.txt", "Hello world")
        print("Success:", res)
    except Exception as e:
        with open("tmp_error.txt", "w") as f:
            f.write(str(e))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
