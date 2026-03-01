import asyncio
import httpx
import json

async def mock_webhook():
    """
    Sends a mock Telegram webhook payload to the local FastAPI server
    to test the entire platform flow end-to-end.
    """
    url = "http://127.0.0.1:8001/telegram/webhook"
    
    # 1. First test: A simple non-tool conversational message
    mock_telegram_update_1 = {
        "update_id": 100000001,
        "message": {
            "message_id": 1,
            "from": {
                "id": 123456789,
                "is_bot": False,
                "first_name": "Test",
                "last_name": "User",
                "username": "testuser"
            },
            "chat": {
                "id": 123456789, # This acts as our session_id
                "type": "private"
            },
            "date": 1709241600,
            "text": "Hi, what do you sell here?"
        }
    }

    # 2. Second test: Explicitly asking for a cake to trigger SearchItemTool
    mock_telegram_update_2 = {
        "update_id": 100000002,
        "message": {
            "message_id": 2,
            "from": {
                "id": 123456789,
                "first_name": "Test",
            },
            "chat": {
                "id": 123456789,
            },
            "text": "I want to buy a cake, what stores have them?"
        }
    }

    async with httpx.AsyncClient() as client:
        print("--- Sending Mock Webhook 1 (Greeting) ---")
        resp1 = await client.post(url, json=mock_telegram_update_1)
        print(f"Server Acknowledged: {resp1.status_code}")
        print(f"Agent Response: {json.dumps(resp1.json(), indent=2)}")
        print("Waiting 10 seconds for the Agent Core to process & Groq to respond...\n")
        await asyncio.sleep(10)
        
        print("--- Sending Mock Webhook 2 (Cake search) ---")
        resp2 = await client.post(url, json=mock_telegram_update_2)
        print(f"Server Acknowledged: {resp2.status_code}")
        print(f"Agent Response: {json.dumps(resp2.json(), indent=2)}")
        print("Check your terminal running 'main.py' to see the logs and Agent actions!")

if __name__ == "__main__":
    asyncio.run(mock_webhook())
