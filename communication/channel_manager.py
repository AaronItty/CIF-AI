"""
Channel manager module.
Orchestrates multiple channels, starts listeners, and registers handlers.
"""

import asyncio
from typing import Dict
from shared.interfaces import BaseChannelHandler


class ChannelManager:
    """
    Manages communication channels and their lifecycles.
    """

    def __init__(self):
        self.channels: Dict[str, BaseChannelHandler] = {}

    def register_channel(self, name: str, handler: BaseChannelHandler):
        """
        Register a new channel handler.
        """
        self.channels[name] = handler

    async def start_all(self):
        """
        Start listening on all registered channels concurrently.
        """

        if not self.channels:
            raise RuntimeError("No communication channels registered.")

        # Create a task for each channel listener
        tasks = []

        for name, handler in self.channels.items():
            if hasattr(handler, "listen") and callable(handler.listen):
                tasks.append(asyncio.create_task(handler.listen()))
            else:
                print(f"[ChannelManager] Channel '{name}' has no listen() method.")

        if not tasks:
            raise RuntimeError("No valid channel listeners to start.")

        # Run all listeners forever
        await asyncio.gather(*tasks)