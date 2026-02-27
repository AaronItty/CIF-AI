import asyncio
import json
from mcp_server.shopping_tools import SearchItemTool, BuyItemTool

async def main():
    print("=== Testing SearchItemTool ===")
    search_tool = SearchItemTool()
    
    # Searching for a generic term to see what is in the database
    item_to_search = "a" 
    print(f"Searching for: '{item_to_search}'")
    
    search_result = await search_tool.execute(item_name=item_to_search)
    print(json.dumps(search_result, indent=2))
    
    if search_result.get("status") == "success" and search_result.get("results"):
        first_item = search_result["results"][0]
        print("\n=== Testing BuyItemTool ===")
        print(f"Attempting to buy: {first_item['item_name']} from store {first_item.get('store_name', first_item['store_id'])}")
        
        buy_tool = BuyItemTool()
        buy_result = await buy_tool.execute(
            store_id=first_item["store_id"],
            product_id=first_item["product_id"],
            quantity=1,
            customer_name="Test User",
            customer_phone="7012079459",
            customer_email="abrahammadamana@gmail.com",
            delivery_address=None
        )
        print(json.dumps(buy_result, indent=2))
    else:
        print("\nSkipping BuyItemTool test because no items were found.")

if __name__ == "__main__":
    asyncio.run(main())
