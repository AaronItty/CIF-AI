"""
Database client initialization.
Handles connection to Supabase.
"""

from shared.config import Config

class SupabaseClient:
    """
    Singleton or connection pool for Supabase database access.
    """
    
    def __init__(self):
        self.url = Config.SUPABASE_URL
        self.key = Config.SUPABASE_KEY
        
    def get_client(self):
        """
        Return the configured Supabase client instance.
        """
        pass
