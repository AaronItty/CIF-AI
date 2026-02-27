"""
Configuration settings for the Agentic AI Platform.
"""

import os

class Config:
    # Supabase Configuration
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
    
    # MCP Server Configuration
    MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000")
    
    # Agent Core Settings
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.85"))
    
    # Communication Channels
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    EMAIL_IMAP_SERVER = os.getenv("EMAIL_IMAP_SERVER", "")
