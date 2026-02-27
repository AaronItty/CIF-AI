"""
State Manager abstraction.
Handles session memory abstraction over the Supabase backend.
"""

from typing import Dict, Any

class StateManager:
    """
    Memory layer for conversational states.
    """
    
    def __init__(self, db_client):
        self.db = db_client
        
    async def get_session_state(self, session_id: str) -> Dict[str, Any]:
        """Fetch full conversation history and context."""
        pass
        
    async def update_session_state(self, session_id: str, diff: Dict[str, Any]):
        """Append or modify session context."""
        pass

    async def log_tool_usage(self, session_id: str, tool_name: str, args: dict, result: dict):
        """Log a specific tool execution within the session context."""
        pass
