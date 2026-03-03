import asyncio
import os
import sys

# Ensure the app root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dashboard.backend.db_client import SupabaseClient

async def main():
    db_client = SupabaseClient().get_client()
    
    # Query pg_proc to see function source
    print("Inspecting 'match_documents' function in DB...")
    res = db_client.table("pg_proc").select("prosrc").eq("proname", "match_documents").execute()
    
    if res.data:
        print("Function Source Code Found:")
        print(res.data[0]['prosrc'])
    else:
        # Maybe it's not in public schema?
        print("Function not found in pg_proc (or not accessible via select on pg_proc).")
        
    # Check if we can see the document_chunks count
    count_res = db_client.table("document_chunks").select("count", count="exact").execute()
    print(f"Total chunks in DB: {count_res.count}")

if __name__ == "__main__":
    asyncio.run(main())
