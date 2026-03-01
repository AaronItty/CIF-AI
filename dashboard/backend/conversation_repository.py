"""
Repository for conversation persistence.
Handles all CRUD operations related to conversations and logs.
"""

from dashboard.backend.db_client import SupabaseClient

class ConversationRepository:
    """
    Abstracts direct Supabase queries for conversation persistence.
    """
    
    def __init__(self, db_client: SupabaseClient):
        self.db = db_client
        
    async def create_conversation(self, user_id: str) -> str:
        """Create a new session record."""
        pass
        
    async def get_history(self, conversation_id: str) -> list:
        """Fetch all messages for a session."""
        pass
        
    async def append_message(self, conversation_id: str, message: dict):
        """Add a new message (user or agent) to the session."""
        pass
