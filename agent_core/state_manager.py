"""
State Manager abstraction.
Handles session memory abstraction over the Supabase backend.
"""

from typing import Dict, Any, List
from shared.data_access.conversation_repository import ConversationRepository

class StateManager:
    """
    Memory layer for conversational states.
    Delegates to ConversationRepository.
    """
    
    def __init__(self, repo: ConversationRepository):
        self.repo = repo
        
    async def get_session_state(self, session_id: str) -> List[Dict[str, Any]]:
        """Fetch full conversation history and context."""
        return await self.repo.get_history(session_id)
        
    async def update_session_state(self, session_id: str, message_data: Dict[str, Any]):
        """Append or modify session context."""
        return await self.repo.append_message(session_id, message_data)

    async def log_tool_usage(self, session_id: str, tool_name: str, args: dict, result: dict):
        """Log a specific tool execution within the session context."""
        log_data = {
            "session_id": session_id,
            "tool_name": tool_name,
            "arguments": args,
            "result": result
        }
        # Assuming the repo has or will have a log_tool method
        return await self.repo.log_tool_usage(session_id, log_data)
    async def update_tags(self, session_id: str, tag: str):
        """Update conversation tags."""
        return await self.repo.update_conversation_tags(session_id, tag)

    async def update_metadata(self, session_id: str, summary: str = None, tags: list = None):
        """Update conversation summary and tags."""
        return await self.repo.update_conversation_metadata(session_id, summary, tags)
