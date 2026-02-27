"""
Email integration handler.
Stateless handler that normalizes input and passes it to Agent Core.
"""

from shared.interfaces import BaseChannelHandler, AgentInterface

class EmailHandler(BaseChannelHandler):
    """
    Handles Email interactions.
    """
    
    def __init__(self, agent: AgentInterface, imap_settings: dict):
        self.agent = agent
        self.imap_settings = imap_settings
        
    async def listen(self):
        """
        Start IMAP listener.
        """
        pass
        
    async def send_message(self, recipient_id: str, message: str) -> bool:
        """
        Send an email response.
        """
        pass
