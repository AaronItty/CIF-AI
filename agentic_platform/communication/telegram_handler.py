"""
Telegram integration handler.
Stateless handler that normalizes input and passes it to Agent Core.
"""

from shared.interfaces import BaseChannelHandler, AgentInterface

class TelegramHandler(BaseChannelHandler):
    """
    Handles Telegram interactions.
    """
    
    def __init__(self, agent: AgentInterface, bot_token: str):
        self.agent = agent
        self.bot_token = bot_token
        
    async def listen(self):
        """
        Start webhook or polling for Telegram.
        """
        pass
        
    async def send_message(self, recipient_id: str, message: str) -> bool:
        """
        Send a Telegram message to a user.
        """
        pass

    async def _handle_incoming(self, update: dict):
        """
        Normalize and pass the Telegram message to the Agent Core.
        """
        pass
