"""
Main entry point for the Hybrid SaaS + Service Agentic AI Platform.

This script wires up the dependencies between the 4 architectural pillars:
1. Communication Layer
2. Agent Core
3. Dashboard & Supabase
4. MCP Server
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from communication.channel_manager import ChannelManager
from communication.telegram_handler import TelegramHandler
from communication.email_handler import EmailHandler
from agent_core.planning_loop import PlanningLoop
from agent_core.reasoning_engine import ReasoningEngine
from agent_core.controller import Controller
from agent_core.state_manager import StateManager
from agent_core.policy_engine import PolicyEngine
from dashboard.db_client import SupabaseClient
from dashboard.dashboard_routes import DashboardRoutes
from agent_core.knowledge_base_service import KnowledgeBaseService
from agent_core.embeddings import EmbeddingService
from mcp_server.server import MCPServer
from mcp_server.tool_registry import ToolRegistry
from mcp_server.permission_manager import PermissionManager

async def launch_mcp_server():
    """Starts the separate MCP server for tools (runs isolated)."""
    registry = ToolRegistry()
    auth = PermissionManager()
    server = MCPServer(registry, auth)
    await server.start()

async def launch_saas_core():
    """Starts the main SaaS application."""
    db_client = SupabaseClient()
    embedding_service = EmbeddingService()
    kb_service = KnowledgeBaseService(db_client, embedding_service)
    
    # Init Dashboard API
    api_app = FastAPI(title="CIF-AI Dashboard API")
    api_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    routes = DashboardRoutes(kb_service)
    routes.register_routes(api_app)
    
    # Run API in background
    import uvicorn
    config = uvicorn.Config(api_app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)
    asyncio.create_task(server.serve())
    
    # Init Core Agent dependencies
    state_manager = StateManager(db_client)
    policy_engine = PolicyEngine()
    reasoning = ReasoningEngine("FAKE_API_KEY")
    # For Controller, we'd pass an MCP Client so it can talk to the isolated server
    controller = Controller(policy_engine=policy_engine, mcp_client=None)

    # Initialize the primary Planning Loop
    agent_loop = PlanningLoop(reasoning, controller, state_manager)
    
    # Initialize Communication Layer
    channels = ChannelManager()
    channels.register_channel("telegram", TelegramHandler(agent=agent_loop, bot_token="TOKEN"))
    channels.register_channel("email", EmailHandler(agent=agent_loop, imap_settings={}))
    
    # Listen forever
    await channels.start_all()

async def main():
    """Run both or selectively based on deployment settings."""
    # In production, these should often run as separate scaled microservices.
    await asyncio.gather(
        launch_mcp_server(),
        launch_saas_core()
    )
    # Keep the event loop running for background servers (FastAPI/MCP)
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
