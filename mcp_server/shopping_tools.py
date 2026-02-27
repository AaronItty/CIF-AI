"""
Shopping tools connecting to the hosted backend via HTTP.
"""

import httpx
from typing import Dict, Any
from mcp_server.base_tool import BaseTool
import os

# Grab the backend URL from environment or use a default mock URL 
HOSTED_BACKEND_URL = os.getenv("HOSTED_BACKEND_URL", "https://api.hosted-backend.example.com")
HOSTED_BACKEND_API_KEY = os.getenv("HOSTED_BACKEND_API_KEY", "demo-key")

class SearchItemTool(BaseTool):
    @property
    def name(self): return "search_item"
    
    @property
    def description(self): return "Search for an item across available stores on the backend."
    
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
        """Call the backend API to search for the item."""
        headers = {"Authorization": f"Bearer {HOSTED_BACKEND_API_KEY}"}
        params = {"q": item_name}
        
        async with httpx.AsyncClient() as client:
            try:
                # Mocking the actual call for demonstration if endpoint is down/not provided
                response = await client.get(f"{HOSTED_BACKEND_URL}/search", params=params, headers=headers)
                response.raise_for_status()
                return response.json()
                
                # Returns mock response reflecting the JSON structure
                return {
                    "status": "success",
                    "results": [
                        {"store": "Store A", "item_name": item_name, "price": 19.99, "in_stock": True},
                        {"store": "Store B", "item_name": item_name, "price": 24.99, "in_stock": True}
                    ]
                }
            except httpx.HTTPError as e:
                return {"status": "error", "message": str(e)}

class BuyItemTool(BaseTool):
    @property
    def name(self): return "buy_item"
    
    @property
    def description(self): return "Buy a specific item from a store using the user's details."
    
    @property
    def schema(self):
        return {
            "type": "object",
            "properties": {
                "item_name": {
                    "type": "string",
                    "description": "Name of the item to purchase."
                },
                "store_name": {
                    "type": "string",
                    "description": "Name of the store to purchase from."
                },
                "login_info": {
                    "type": "string",
                    "description": "Login context or token for the user on the store."
                },
                "address": {
                    "type": "string",
                    "description": "Delivery address."
                },
                "phone_number": {
                    "type": "string",
                    "description": "User's phone number."
                },
                "email": {
                    "type": "string",
                    "description": "User's gmail address."
                }
            },
            "required": ["item_name", "store_name", "login_info", "address", "phone_number", "email"]
        }
        
    async def execute(self, item_name: str, store_name: str, login_info: str, address: str, phone_number: str, email: str) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {HOSTED_BACKEND_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "item_name": item_name,
            "store_name": store_name,
            "login_info": login_info,
            "shipping": {
                "address": address,
                "phone": phone_number,
                "email": email
            }
        }
        
        async with httpx.AsyncClient() as client:
            try:
                # Mock transaction if no live endpoint is provided
                response = await client.post(f"{HOSTED_BACKEND_URL}/buy", json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
                
                return {
                    "status": "success",
                    "transaction_id": "TXN-987654321",
                    "message": f"Successfully purchased {item_name} from {store_name}. Confirmation sent to {email}."
                }
            except httpx.HTTPError as e:
                return {"status": "error", "message": str(e)}
