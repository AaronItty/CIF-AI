"""
Canonical location for the Supabase database client.
All server-side code should import SupabaseClient from here.
"""

from supabase import create_client, Client
from shared.config import Config

class SupabaseClient:
    """
    Singleton-style wrapper for Supabase database access.
    Uses the service role key for full server-side access.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseClient, cls).__new__(cls)
            cls._instance.url = Config.SUPABASE_URL
            cls._instance.key = Config.SUPABASE_KEY
            if not cls._instance.url or not cls._instance.key:
                # Fallback for dev if env is not loaded correctly
                print("SUPABASE_URL or SUPABASE_KEY not found in .env file")
            cls._instance.client: Client = create_client(cls._instance.url, cls._instance.key)
        return cls._instance
        
    def get_client(self) -> Client:
        """
        Return the configured Supabase client instance.
        """
        return self.client
