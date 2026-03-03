import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

from agent_core.reasoning_engine import ReasoningEngine
from agent_core.controller import Controller
from agent_core.state_manager import StateManager
from agent_core.policy_engine import PolicyEngine
from agent_core.planning_loop import PlanningLoop
from shared.data_access.db_client import SupabaseClient
from shared.data_access.conversation_repository import ConversationRepository
from communication.schemas.normalized_message import NormalizedMessage

load_dotenv()

app = FastAPI(title="CIF-AI Agent Core Service (Layer 2)")

# Initialize Dependencies
LLM_API_KEY = os.getenv("LLM_API_KEY", "")

db_client = SupabaseClient()
convo_repo = ConversationRepository(db_client)
state_manager = StateManager(convo_repo)
reasoning_engine = ReasoningEngine(api_key=LLM_API_KEY)
policy_engine = PolicyEngine()
controller = Controller(
    policy_engine=policy_engine,
    mcp_server_url=os.getenv("MCP_SERVER_URL", "http://localhost:8004"),
    mcp_shared_secret=os.getenv("MCP_SHARED_SECRET", "super-secret-mcp-key-123")
)
planning_loop = PlanningLoop(reasoning_engine, controller, state_manager)

@app.post("/api/v1/process_message")
async def process_message(msg: NormalizedMessage):
    """
    Standard ingestion point for all Layer 1 communication services.
    """
    try:
        result = await planning_loop.process_message(msg)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
