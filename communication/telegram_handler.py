"""
Telegram integration handler (Webhook Mode).
"""

import httpx
from typing import Optional

from shared.interfaces import BaseChannelHandler, AgentInterface
from communication.schemas.normalized_message import NormalizedMessage


class TelegramHandler(BaseChannelHandler):

    TELEGRAM_API_BASE = "https://api.telegram.org"

    def __init__(self, agent: AgentInterface, bot_token: str):
        self.agent = agent
        self.bot_token = bot_token
        print(bot_token)
        self._api_url = f"{self.TELEGRAM_API_BASE}/bot{self.bot_token}"

    async def listen(self):
        """
        Not used in webhook mode.
        """
        return

    async def send_message(self, recipient_id: str, message: str) -> bool:
        url = f"{self._api_url}/sendMessage"

        payload = {
            "chat_id": recipient_id,
            "text": message
        }

        print("➡ Sending to Telegram:", payload)
        print("➡ URL:", url)

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)

        print("⬅ Status:", response.status_code)
        print("⬅ Response:", response.text)

        return response.status_code == 200
    async def _handle_incoming(self, update: dict):
        message_block = update.get("message")
        if not message_block:
            return

        user = message_block.get("from")
        chat = message_block.get("chat")
        text = message_block.get("text")
        print("1️⃣ Update received")

        message_block = update.get("message")
        print("2️⃣ Message block:", message_block)

        if not message_block:
            print("No message block")
            return
        if not user or not chat or not text:
            return

        normalized = NormalizedMessage(
            user_id=str(user["id"]),
            session_id=str(chat["id"]),
            message=text,
            channel="telegram"
        )

        response = await self.agent.process_message(normalized)

        if response and response.get("text"):
            await self.send_message(normalized.session_id, response["text"])