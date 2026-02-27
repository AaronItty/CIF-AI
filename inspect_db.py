import asyncio
import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

async def main():
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    
    schema_info = {}
    try:
        res = supabase.table("products").select("*").limit(1).execute()
        if res.data:
            schema_info["products"] = list(res.data[0].keys())
    except Exception as e:
        schema_info["products_error"] = str(e)

    try:
        res = supabase.table("stores").select("*").limit(1).execute()
        if res.data:
            schema_info["stores"] = list(res.data[0].keys())
    except Exception as e:
        schema_info["stores_error"] = str(e)

    with open("schema.txt", "w") as f:
        json.dump(schema_info, f, indent=2)

if __name__ == "__main__":
    asyncio.run(main())
