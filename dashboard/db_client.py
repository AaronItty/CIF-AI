"""
Database client initialization.
Handles connection to Supabase.
"""

from shared.config import Config
from supabase import create_client, Client

class SupabaseClient:
    """
    Singleton or connection pool for Supabase database access.
    """
    
    def __init__(self):
        self.url = Config.SUPABASE_URL
        self.key = Config.SUPABASE_KEY
        # Create singleton connection to Supabase
        self.client: Client = create_client(self.url, self.key)
        
    def get_client(self) -> Client:
        """
        Return the configured Supabase client instance.
        """
        return self.client
