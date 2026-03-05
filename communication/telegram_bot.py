import logging
import os
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class TelegramBot:
    def __init__(self, token: str, agent_url: str):
        self.token = token
        self.agent_url = agent_url

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Extracts user message, forwards to Agent Core, and returns the response.
        """
        if not update.message or not update.message.text:
            return

        user_id = str(update.effective_user.id)
        session_id = str(update.effective_chat.id)
        message_text = update.message.text

        # Prepare payload for Agent Core (NormalizedMessage schema)
        payload = {
            "user_id": user_id,
            "session_id": session_id,
            "message": message_text,
            "channel": "telegram"
        }

        logging.info(f"Forwarding message from {user_id} to Agent Core")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.agent_url,
                    json=payload,
                    timeout=60.0  # Agent might take time to reason
                )
                response.raise_for_status()
                data = response.json()
                
                # Extract agent's text response
                agent_response = data.get("response", "I'm sorry, I couldn't process that.")
                
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=agent_response
                )
        except Exception as e:
            logging.error(f"Error communicating with Agent Core: {e}")
            await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="⚠️ Error: I'm having trouble connecting to my brain. Please try again later."
            )

    def run(self):
        """Starts the bot in polling mode."""
        application = ApplicationBuilder().token(self.token).build()
        
        message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), self.handle_message)
        application.add_handler(message_handler)

        logging.info("Telegram bot started in polling mode...")
        application.run_polling()

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    agent_url = os.getenv("AGENT_CORE_URL", "http://localhost:8002/api/v1/process_message")

    if not token:
        print("Error: TELEGRAM_BOT_TOKEN not found in environment.")
    else:
        bot = TelegramBot(token, agent_url)
        bot.run()
