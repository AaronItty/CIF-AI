import os
import sys
from dotenv import load_dotenv
from communication.telegram_bot import TelegramBot

def main():
    load_dotenv()

    # Telegram Bot Configuration
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    # Point to the Agent Core FastAPI service (default port 8002)
    agent_url = os.getenv("AGENT_CORE_URL", "http://localhost:8002/api/v1/process_message")

    if not token:
        print("❌ Error: TELEGRAM_BOT_TOKEN not found in .env file.")
        print("Please add your bot token to the .env file and try again.")
        sys.exit(1)

    print("🚀 Starting CIF-AI Telegram Bot...")
    print(f"🔗 Connected to Agent Core at: {agent_url}")
    print("Use Ctrl+C to stop.")

    try:
        bot = TelegramBot(token, agent_url)
        bot.run()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped manually.")
    except Exception as e:
        print(f"❌ Critical error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
