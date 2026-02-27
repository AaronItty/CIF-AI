"""
Shopping tools connecting to the hosted backend via HTTP and Supabase.
"""

import os
import httpx
from typing import Dict, Any, Optional
from mcp_server.base_tool import BaseTool
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

class SearchItemTool(BaseTool):
    @property
    def name(self): return "search_item"
    
    @property
    def description(self): return "Search for an item across available stores on the backend to find store_id and product_id."
    
    @property
    def schema(self):
        return {
            "type": "object",
            "properties": {
                "item_name": {
                    "type": "string",
                    "description": "Name of the item to search for."
                }
            },
            "required": ["item_name"]
        }
        
    async def execute(self, item_name: str) -> Dict[str, Any]:
        """Call the Supabase database to search for the item."""
        if not SUPABASE_URL or not SUPABASE_ANON_KEY:
            return {"status": "error", "message": "Supabase credentials missing."}
            
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        
        try:
            # Search for available products matching the name
            products_res = supabase.table("products").select("id, name, price, store_id").ilike("name", f"%{item_name}%").eq("is_in_stock", True).execute()
            products = products_res.data
            
            if not products:
                return {"status": "success", "results": [], "message": f"No in-stock items found matching '{item_name}'."}
                
            # Get the store details
            store_ids = list(set([p["store_id"] for p in products if p.get("store_id")]))
            stores_res = supabase.table("stores").select("id, store_name").in_("id", store_ids).execute()
            stores = {s["id"]: s["store_name"] for s in stores_res.data}
            
            results = []
            for p in products:
                results.append({
                    "product_id": p["id"],
                    "item_name": p["name"],
                    "price": p["price"],
                    "store_id": p["store_id"],
                    "store_name": stores.get(p["store_id"], "Unknown Store")
                })
                
            return {
                "status": "success",
                "results": results
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
        return {"status": "error", "message": "Unknown error."}

class BuyItemTool(BaseTool):
    @property
    def name(self): return "buy_item"
    
    @property
    def description(self): return "Place an order for a specific item using product_id and store_id from the search_item results."
    
    @property
    def schema(self):
        return {
            "type": "object",
            "properties": {
                "store_id": {
                    "type": "string",
                    "description": "ID of the store."
                },
                "product_id": {
                    "type": "string",
                    "description": "ID of the product being purchased."
                },
                "quantity": {
                    "type": "integer",
                    "description": "Quantity to purchase.",
                    "default": 1
                },
                "customer_name": {
                    "type": "string",
                    "description": "Name of the customer."
                },
                "customer_phone": {
                    "type": "string",
                    "description": "Customer's phone number."
                },
                "customer_email": {
                    "type": "string",
                    "description": "Customer's email address."
                },
                "delivery_address": {
                    "type": "string",
                    "description": "Delivery address (if pickup, can be null or empty)."
                }
            },
            "required": ["store_id", "product_id", "quantity", "customer_name", "customer_phone", "customer_email"]
        }
        
    async def execute(self, store_id: str, product_id: str, quantity: int, customer_name: str, customer_phone: str, customer_email: str, delivery_address: Optional[str] = None) -> Dict[str, Any]:
        if not SUPABASE_URL:
            return {"status": "error", "message": "Supabase URL missing."}
            
        endpoint = f"{SUPABASE_URL}/functions/v1/Place-Order"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}" # Edge functions usually require anon key
        }
        
        import uuid
        
        payload = {
            "checkout_session_id": str(uuid.uuid4()),
            "store_id": store_id,
            "customer": {
                "name": customer_name,
                "phone": customer_phone,
                "email": customer_email
            },
            "delivery": {
                "method": "pickup" if not delivery_address else "delivery",
                "address": delivery_address,
                "lat": None,
                "lng": None,
                "date": None,
                "time_slot": None,
                "pincode": None,
                "landmark": None,
                "notes": None
            },
            "items": [
                {
                    "product_id": product_id,
                    "quantity": quantity,
                    "variant": None,
                    "custom_note": "Order placed via AI Agent"
                }
            ],
            "notes": "Any global order notes go here",
            "payment_method": "online"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(endpoint, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                return {
                    "status": "success",
                    "payment_link_url": data.get("payment_link_url"),
                    "message": "Order placed successfully. Please review the payment link."
                }
            except httpx.HTTPError as e:
                error_body = ""
                if hasattr(e, 'response') and e.response:
                    error_body = e.response.text
                return {"status": "error", "message": f"HTTP Error: {str(e)}", "details": error_body}
        return {"status": "error", "message": "Unknown error."}
