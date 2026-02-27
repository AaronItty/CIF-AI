"""
Dashboard API Endpoints.
Provides backend-ready endpoints for the frontend application.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

class DashboardRoutes:
    """
    Registers API routes to expose analytical data and system status.
    """
    
    def __init__(self, analytics: 'AnalyticsService', conversation_repo: 'ConversationRepository'):
        self.analytics = analytics
        self.repo = conversation_repo
        self.router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])
        self._register_routes()
        
    def _register_routes(self):
        """
        Register GET/POST handlers for dashboard consumers.
        """
        
        @self.router.get("/stats/escalations")
        async def get_escalation_stats():
            """Returns the percentage of escalated conversations."""
            rate = await self.analytics.get_escalation_rate()
            return {"escalation_rate_percentage": rate}
            
        @self.router.get("/stats/tools")
        async def get_top_tools():
            """Returns the most frequently invoked tools."""
            tools = await self.analytics.get_top_tools()
            return {"top_tools": tools}
            
        @self.router.get("/conversations/{session_id}")
        async def get_conversation_history(session_id: str):
            """Returns the full message history for a given session."""
            history = await self.repo.get_history(session_id)
            if not history:
                raise HTTPException(status_code=404, detail="Conversation not found")
            return {"history": history}

    def get_router(self) -> APIRouter:
        return self.router
