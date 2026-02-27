"""
Example external tools demonstrating boundary enforcement.
Includes RefundTool, TicketBookingTool (Mock), InventoryCheckTool (Mock).
"""

from typing import Dict, Any
from mcp_server.base_tool import BaseTool

class RefundTool(BaseTool):
    @property
    def name(self): return "process_refund"
    
    @property
    def description(self): return "Processes a refund for a given order ID."
    
    @property
    def schema(self):
        return {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"}
            },
            "required": ["order_id"]
        }
        
    async def execute(self, order_id: str) -> Dict[str, Any]:
        """Mock refund logic to external payment gateway via MCP interface."""
        return {"status": "success", "message": f"Refund processed for {order_id}"}


class TicketBookingTool(BaseTool):
    @property
    def name(self): return "book_ticket"
    
    @property
    def description(self): return "Books a support or flight ticket."
    
    @property
    def schema(self):
        return {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "details": {"type": "string"}
            },
            "required": ["user_id", "details"]
        }
        
    async def execute(self, user_id: str, details: str) -> Dict[str, Any]:
        return {"status": "success", "ticket_id": "TKT-12345"}


class InventoryCheckTool(BaseTool):
    @property
    def name(self): return "check_inventory"
    
    @property
    def description(self): return "Checks backend product database for inventory count."
    
    @property
    def schema(self):
        return {
            "type": "object",
            "properties": {
                "sku": {"type": "string"}
            },
            "required": ["sku"]
        }
        
    async def execute(self, sku: str) -> Dict[str, Any]:
        return {"status": "success", "inventory_count": 42}
