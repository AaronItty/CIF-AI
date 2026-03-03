import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from shared.data_access.db_client import SupabaseClient
from agent_core.embeddings import EmbeddingService
from dashboard.backend.knowledge_base_service import KnowledgeBaseService
from dashboard.backend.dashboard_routes import DashboardRoutes

# Load environment variables
load_dotenv()

print("Initializing Knowledge Base Service...")

# 1. Initialize dependencies
db_client = SupabaseClient()
embedding_service = EmbeddingService()

# 2. Initialize the KB service itself
kb_service = KnowledgeBaseService(db_client=db_client, embedding_service=embedding_service)

# 3. Setup FastAPI and middleware
app = FastAPI(title="CIF-AI Knowledge Base Service (Dedicated)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For local dev, allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Mount the routes
dashboard_routes = DashboardRoutes(kb_service=kb_service)
dashboard_routes.register_routes(app)

if __name__ == "__main__":
    print("▶ Starting Dedicated Knowledge Base API on port 8000...")
    uvicorn.run("app-service:app", host="0.0.0.0", port=8000, reload=True)
