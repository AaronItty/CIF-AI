"""
Standard unified interface definitions for service integrations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseTool(ABC):
    """
    Base abstraction enforcing uniform execution interface for all skills.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier of the tool."""
        pass
        
    @property
    @abstractmethod
    def description(self) -> str:
        """Instruction injected into the LLM context regarding usage."""
        pass
        
    @property
    @abstractmethod
    def schema(self) -> dict:
        """JSON Schema format for expected parameters."""
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool's core logic with the validation bounds.
        Returns uniform dictionary result.
        """
        pass
