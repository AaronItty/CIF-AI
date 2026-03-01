"""
Escalation routing module.
Handles routing the conversation to a human operator when the Agent Core triggers an escalation.
"""

from dashboard.backend.db_client import SupabaseClient

class EscalationRouter:
    """
    Routes escalated sessions to human operators based on policies and availability.
    """
    
    def __init__(self, db_client: SupabaseClient):
        self.db = db_client
        
    async def route_to_human(self, session_id: str, reason: str, context: dict) -> bool:
        """
        Open a human handoff channel (e.g., in the Dashboard or via dedicated support tool).
        Updates the conversation status to 'escalated'.
        """
        try:
            # 1. Update the conversation status so Agent Core ignores future messages
            # self.db.client.table("conversations").update({"status": "escalated"}).eq("id", session_id).execute()
            print(f"[MOCKED DB] Routing to human: Status set to escalated for {session_id}")
            
            # 2. Log the escalation to the 'escalations' table for the Dashboard UI
            # self.db.client.table("escalations").insert({
            #     "conversation_id": session_id,
            #     "reason": reason,
            #     "status": "pending_operator",
            #     "context": context
            # }).execute()
            print(f"[MOCKED DB] Escalation reason logged for {session_id}: {reason}")
            return True
        except Exception as e:
            print(f"Failed to escalate {session_id}: {e}")
            return False

    async def close_escalation(self, session_id: str):
        """
        Return control back to the AI after human operator finishes.
        """
        try:
            # 1. Put the conversation back to active
            # self.db.client.table("conversations").update({"status": "active"}).eq("id", session_id).execute()
            print(f"[MOCKED DB] Closing escalation: Status set back to active for {session_id}")
            
            # 2. Mark the escalation as resolved
            # self.db.client.table("escalations").update({"status": "resolved"}).eq("conversation_id", session_id).execute()
            print(f"[MOCKED DB] Escalation logged as resolved for {session_id}")
            return True
        except Exception as e:
            print(f"Failed to close escalation {session_id}: {e}")
            return False
