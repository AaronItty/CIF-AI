"""
Tool Registry module.
Maintains available skills/tools and maps identifiers to implementations.
"""

from typing import Dict, Type
from mcp_server.base_tool import BaseTool

class ToolRegistry:
    """
    Registry for organizing and discovering available specific-service tools.
    """
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        
    def register(self, tool: BaseTool):
        """
        Register a tool instance for availability.
        """
        self._tools[tool.name] = tool
        
    def get_tool(self, tool_name: str) -> BaseTool:
        """
        Retrieve a registered tool by its name.
        """
        pass
        
    def list_available(self) -> list:
        """
        Get schemas for all registered tools to advertise to the Agent Core.
        """
        pass
