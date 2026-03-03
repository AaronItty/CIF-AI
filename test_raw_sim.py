import asyncio
import os
import sys

# Ensure the app root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dashboard.backend.db_client import SupabaseClient
from agent_core.embeddings import EmbeddingService

async def main():
    db_client = SupabaseClient().get_client()
    embed_service = EmbeddingService()
    
    query = "Where is the bakery?"
    query_vec = embed_service.embed_query(query)
    # Convert list to string for SQL: '[0.1, 0.2, ...]'
    vec_str = "[" + ",".join([str(x) for x in query_vec]) + "]"
    
    # We can try to use standard select with filter or order
    print(f"Testing raw similarity for query: {query}")
    
    # First, get any chunk
    res = db_client.table("document_chunks").select("id, content, embedding").limit(1).execute()
    if res.data:
        chunk = res.data[0]
        chunk_id = chunk['id']
        print(f"Checking Chunk ID: {chunk_id}")
        
        # We can't do raw similarity in .select() via the client easily without an RPC
        # BUT we can check if it returns via any existing rpc or just check the count
        
        # Let's try to use the RPC but with a REALLY low threshold like -1.0
        rpc_res = db_client.rpc("match_documents", {
            "query_embedding": query_vec,
            "match_threshold": -1.0,
            "match_count": 5
        }).execute()
        
        print(f"RPC (-1.0 threshold) Results count: {len(rpc_res.data)}")
        if rpc_res.data:
            print(f"Top result similarity: {rpc_res.data[0].get('similarity')}")
        else:
            print("Still no results even with -1.0 threshold!")
            
    else:
        print("No chunks found in DB.")

if __name__ == "__main__":
    asyncio.run(main())
