import os
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
import uvicorn

from dashboard.db_client import SupabaseClient
from dashboard.conversation_repository import ConversationRepository
from dashboard.analytics_service import AnalyticsService
from dashboard.dashboard_routes import DashboardRoutes

from agent_core.state_manager import StateManager
from agent_core.policy_engine import PolicyEngine
from agent_core.reasoning_engine import ReasoningEngine
from agent_core.controller import Controller
from agent_core.planning_loop import PlanningLoop

from communication.telegram_handler import TelegramHandler
from communication.channel_manager import ChannelManager
from communication.escalation_router import EscalationRouter

load_dotenv()

# Env vars
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8000")
MCP_SHARED_SECRET = os.getenv("MCP_SHARED_SECRET", "super-secret-mcp-key-123")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# 1. Dashboard / DB init
db_client = SupabaseClient()
convo_repo = ConversationRepository(db_client)
analytics_svc = AnalyticsService(db_client)

# 2. Core init
state_manager = StateManager(convo_repo)
policy_engine = PolicyEngine()
reasoning_engine = ReasoningEngine(api_key=LLM_API_KEY)
controller = Controller(policy_engine=policy_engine, mcp_server_url=MCP_SERVER_URL, mcp_shared_secret=MCP_SHARED_SECRET)
planning_loop = PlanningLoop(reasoning_engine, controller, state_manager)

# 3. Communication init
print(BOT_TOKEN)
telegram_handler = TelegramHandler(agent=planning_loop, bot_token=BOT_TOKEN)
channel_manager = ChannelManager()
channel_manager.register_channel("telegram", telegram_handler)
escalation_router = EscalationRouter(db_client)

# 4. FastAPI Setup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Hook for channel manager polling if needed later
    yield
    pass

app = FastAPI(title="SaaS Core Logic & Dashboard API", lifespan=lifespan)

# Register Dashboard UI routes
dashboard_routes = DashboardRoutes(analytics=analytics_svc, conversation_repo=convo_repo)
app.include_router(dashboard_routes.get_router())

# Telegram Webhook endpoint
@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    update = await request.json()
    result = await telegram_handler._handle_incoming(update)
    return {"status": "ok", "agent_response": result}

if __name__ == "__main__":
    print("▶ Starting SaaS Core APIs on port 8001...")
    print("Dashboard Routes mounted at: /api/dashboard")
    print("Telegram Webhook mounted at: /telegram/webhook")
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
