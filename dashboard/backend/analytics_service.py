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
        pass
        
    async def get_top_tools(self) -> list:
        """
        Return the most frequently invoked tools.
        """
        pass
