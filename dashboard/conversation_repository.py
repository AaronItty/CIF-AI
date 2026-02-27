"""
Repository for conversation persistence.
Handles all CRUD operations related to conversations and logs.
"""

from dashboard.db_client import SupabaseClient
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
        # resp = self.db.client.table("conversations").insert({"id": new_id, "user_id": user_id, "channel": channel, "status": "active"}).execute()
        # if resp.data:
        #     return resp.data[0]["id"]
        # return None
        print(f"[MOCKED DB] Created conversation for {user_id}")
        return new_id
        
    async def get_history(self, conversation_id: str) -> list:
        """Fetch all messages for a session."""
        cid = _make_uuid(conversation_id)
        # resp = self.db.client.table("messages").select("*").eq("conversation_id", cid).order("created_at").execute()
        # return resp.data
        print(f"[MOCKED DB] Fetching history for {cid}")
        return []
        
    async def append_message(self, conversation_id: str, message: dict):
        """Add a new message (user or agent) to the session."""
        cid = _make_uuid(conversation_id)
        user_id = message.pop("user_id", "unknown_user")
        channel = message.pop("channel", "unknown_channel")
        
        # Upsert the conversation if it doesn't exist
        try:
            # self.db.client.table("conversations").upsert({
            #     "id": cid,
            #     "user_id": user_id,
            #     "channel": channel,
            #     "status": "active"
            # }, on_conflict="id").execute()
            pass
        except Exception:
            pass # Probably already exists with active or escalated
            
        # Construct a strict payload for the messages table
        payload = {
            "conversation_id": cid,
            "role": message.get("role", "system"),
            "content": message.get("content", "")
        }
            
        # resp = self.db.client.table("messages").insert(payload).execute()
        # return resp.data
        print(f"[MOCKED DB] Logged message for {cid}: {payload['role']}")
        return [payload]
        
    async def log_tool_usage(self, session_id: str, log_data: dict):
        """Log tool execution"""
        cid = _make_uuid(session_id)
        # Construct a strict payload for the tool_logs table
        payload = {
            "conversation_id": cid,
            "tool_name": log_data.get("tool_name", "unknown"),
            "arguments": log_data.get("arguments", {}),
            "result": log_data.get("result", {})
        }
        
        # resp = self.db.client.table("tool_logs").insert(payload).execute()
        # return resp.data
        print(f"[MOCKED DB] Logged tool usage for {cid}: {payload['tool_name']}")
        return [payload]

