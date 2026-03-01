"""
Data analytics service.
Provides aggregation and stats for the Dashboard UI.
"""

from dashboard.backend.db_client import SupabaseClient

class AnalyticsService:
    """
    Generates statistics on escalations, tool usage, and overall platform load.
    """
    
    def __init__(self, db_client: SupabaseClient):
        self.db = db_client
        
    async def get_escalation_rate(self) -> float:
        """
        Calculate percentage of conversations ending up escalated.
        """
        try:
            # Get total conversations
            total_resp = self.db.client.table("conversations").select("id", count="exact").execute()
            total_count = total_resp.count if total_resp.count is None else 0
            
            # Get escalated conversations
            esc_resp = self.db.client.table("conversations").select("id", count="exact").eq("status", "escalated").execute()
            esc_count = esc_resp.count if esc_resp.count is None else 0
            
            if total_count == 0:
                return 0.0
                
            return (esc_count / total_count) * 100.0
        except Exception as e:
            print(f"Stats Error: {e}")
            return 0.0
        
    async def get_top_tools(self) -> list:
        """
        Return the most frequently invoked tools.
        """
        try:
            # A real grouping query requires RPC or processing in python.
            # We will fetch recent logs and manually aggregate for anMVP.
            resp = self.db.client.table("tool_logs").select("tool_name").limit(100).execute()
            freq = {}
            for log in resp.data:
                freq[log["tool_name"]] = freq.get(log["tool_name"], 0) + 1
                
            sorted_tools = sorted(freq.items(), key=lambda x: x[1], reverse=True)
            return sorted_tools
        except Exception as e:
            print(f"Stats Error: {e}")
            return []
