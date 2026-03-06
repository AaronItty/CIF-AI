import os
import logging
from dotenv import load_dotenv
from communication.telegram_bot import TelegramBot

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

if __name__ == "__main__":
    load_dotenv()

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    # Inside Docker, we should use the service name 'agent-core'
    agent_url = os.getenv("AGENT_CORE_URL", "http://agent-core:8002/api/v1/process_message")

    if not token:
        logging.error("Error: TELEGRAM_BOT_TOKEN not found in environment.")
    else:
        logging.info("Starting Telegram Bot via dedicated launcher...")
        bot = TelegramBot(token, agent_url)
        bot.run()
