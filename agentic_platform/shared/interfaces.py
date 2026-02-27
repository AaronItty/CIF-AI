"""
Shared interfaces for the Agentic AI Platform.

This module defines the boundaries between the 4 major components:
- Communication Layer
- Agent Core
- Dashboard + Supabase
- MCP Server (Service Layer)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseChannelHandler(ABC):
    """
    Interface for communication channel handlers (Telegram, Email, Call).
    Must remain stateless where possible and only communicate with Agent Core.
    """
    
    @abstractmethod
    async def listen(self):
        """Listen for incoming messages on the channel."""
        pass
        
    @abstractmethod
    async def send_message(self, recipient_id: str, message: str) -> bool:
        """Send a message through the channel."""
        pass

class AgentInterface(ABC):
    """
    Interface for the Agent Core to be called by the Communication Layer.
    """
    
    @abstractmethod
    async def process_message(self, user_id: str, session_id: str, message: str, channel: str) -> Dict[str, Any]:
        """
        Process an incoming message. Returns the agent's response or an escalation trigger.
        """
        pass

class ToolExecutionInterface(ABC):
    """
    Interface for executing tools on the isolated MCP server.
    """
    
    @abstractmethod
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool via the MCP API boundary.
        """
        pass
