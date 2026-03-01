"""
Repository for conversation persistence.
Handles all CRUD operations related to conversations and logs.
"""

from dashboard.backend.db_client import SupabaseClient
import uuid

def _make_uuid(session_id: str) -> str:
    # Ensure strings like '123456789' are mapped to a valid UUID for Supabase
    try:
        uuid.UUID(session_id)
        return session_id
    except ValueError:
        return str(uuid.uuid5(uuid.NAMESPACE_OID, str(session_id)))

class ConversationRepository:
    """
    Abstracts direct Supabase queries for conversation persistence.
    """
    
    def __init__(self, db_client: SupabaseClient):
        self.db = db_client
        
        
    async def create_conversation(self, user_id: str, channel: str = "unknown") -> str:
        """Create a new session record."""
        new_id = str(uuid.uuid4())
        from shared.config import Config
        resp = self.db.client.table("conversations").insert({
            "id": new_id, 
            "user_id": user_id, 
            "channel_id": None, # Mapping to channel table later
            "organization_id": Config.DEFAULT_ORG_ID,
            "status": "active"
        }).execute()
        
        if resp.data:
            return resp.data[0]["id"]
        return new_id
        
    async def get_history(self, conversation_id: str) -> list:
        """Fetch all messages for a session."""
        cid = _make_uuid(conversation_id)
        resp = self.db.client.table("messages").select("*").eq("session_id", cid).order("created_at").execute()
        return resp.data
        
    async def append_message(self, conversation_id: str, message: dict):
        """Add a new message (user or agent) to the session."""
        cid = _make_uuid(conversation_id)
        raw_user_id = message.pop("user_id", "unknown_user")
        user_uuid = _make_uuid(raw_user_id)
        channel = message.pop("channel", "unknown_channel")
        from shared.config import Config
        
        # 1. Ensure the USER exists (Foreign Key for Conversations)
        try:
            self.db.client.table("users").upsert({
                "id": user_uuid,
                "organization_id": Config.DEFAULT_ORG_ID,
                "full_name": "Test User",
                "email": f"{raw_user_id}@example.com" if "@" not in raw_user_id else raw_user_id
            }, on_conflict="id").execute()
        except Exception as e:
            print(f"User Upsert Warning: {e}")

        # 2. Ensure the CONVERSATION exists (Foreign Key for Messages)
        try:
            self.db.client.table("conversations").upsert({
                "id": cid,
                "user_id": user_uuid, 
                "organization_id": Config.DEFAULT_ORG_ID,
                "status": "active"
            }, on_conflict="id").execute()
        except Exception as e:
            print(f"Conversation Upsert Warning: {e}")
            
        # 3. Insert the MESSAGE
        payload = {
            "session_id": cid,
            "organization_id": Config.DEFAULT_ORG_ID,
            "role": message.get("role", "user"), 
            "content": message.get("content", ""),
            "type": "text"
        }
            
        resp = self.db.client.table("messages").insert(payload).execute()
        return resp.data
        
    async def log_tool_usage(self, session_id: str, log_data: dict):
        """Log tool execution"""
        cid = _make_uuid(session_id)
        from shared.config import Config
        # Note: Tool logs in current schema might be in a different table or JSONB field in messages
        payload = {
            "conversation_id": cid,
            "tool_name": log_data.get("tool_name", "unknown"),
            "arguments": log_data.get("arguments", {}),
            "result": log_data.get("result", {})
        }
        
        # Checking if tool_logs table exists or logging to metadata
        try:
            self.db.client.table("tool_logs").insert(payload).execute()
        except Exception:
            pass # Fallback if table doesn't exist yet
        return [payload]

