import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Config:

    # Supabase Configuration
    SUPABASE_URL = os.getenv("OUR_SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("OUR_SUPABASE_ANON_KEY", "")
    DEFAULT_ORG_ID = os.getenv("DEFAULT_ORG_ID", "302945a7-2a4b-4b78-a764-daa12777fbaf")
    
    # MCP Server Configuration
    MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000")
    
    # Agent Core Settings
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.85"))
    
    # Communication Channels
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    EMAIL_IMAP_SERVER = os.getenv("EMAIL_IMAP_SERVER", "")
