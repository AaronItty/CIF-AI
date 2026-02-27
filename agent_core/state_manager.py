"""
State Manager abstraction.
Handles session memory abstraction over the Supabase backend.
"""

from typing import Dict, Any, List
from supabase import Client

class StateManager:
    """
    Memory layer for conversational states.
    """
    
    def __init__(self, db_client: Client):
        self.db = db_client
        
    async def get_session_state(self, session_id: str) -> List[Dict[str, Any]]:
        """Fetch full conversation history and context."""
        # Query the 'messages' table for the given session_id, ordered by creation time
        response = self.db.table("messages").select("*").eq("session_id", session_id).order("created_at").execute()
        return response.data
        
    async def update_session_state(self, session_id: str, message_data: Dict[str, Any]):
        """Append or modify session context."""
        # Ensure the message is linked to the correct session
        message_data["session_id"] = session_id
        # Insert the new message record into the 'messages' table
        response = self.db.table("messages").insert(message_data).execute()
        return response.data

    async def log_tool_usage(self, session_id: str, tool_name: str, args: dict, result: dict):
        """Log a specific tool execution within the session context."""
        log_data = {
            "session_id": session_id,
            "tool_name": tool_name,
            "arguments": args,
            "result": result
        }
        # Insert audit trail into a 'tool_logs' table mapping to the session
        response = self.db.table("tool_logs").insert(log_data).execute()
        return response.data
