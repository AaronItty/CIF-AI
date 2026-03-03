import os
import httpx
import asyncio
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

from communication.email_handler import EmailHandler
from communication.schemas.normalized_message import NormalizedMessage

load_dotenv()

app = FastAPI(title="CIF-AI Email Communication Service (Layer 1)")

AGENT_CORE_URL = os.getenv("AGENT_CORE_URL", "http://localhost:8002/api/v1/process_message")

class SendEmailRequest(BaseModel):
    recipient_id: str
    message: str

# Use the existing EmailHandler but patch its agent interaction
class EmailServiceHandler(EmailHandler):
    def __init__(self, agent_url: str, gmail_settings: dict = None):
        # Pass None as agent because we will override the call
        super().__init__(agent=None, gmail_settings=gmail_settings)
        self.agent_url = agent_url

    async def listen(self):
        """
        Modified listener that POSTs to the Agent Core Service instead of calling a Python method.
        """
        print(f"Started Gmail API Microservice listener (Target: {self.agent_url})...")
        try:
            while True:
                if not self.service:
                    self.service = self._authenticate()
                    
                if not self.service:
                    print("[Gmail API] Not authenticated. Waiting for token.json (connect via Dashboard)...")
                    await asyncio.sleep(10)
                    continue

                print("Polling Gmail for unread messages...")
                loop = asyncio.get_event_loop()
                results = await loop.run_in_executor(
                    None, 
                    lambda: self.service.users().messages().list(userId='me', q='is:unread').execute()
                )
                
                messages = results.get('messages', [])
                print(f"Found {len(messages)} unread messages.")
                
                async with httpx.AsyncClient() as client:
                    for message_info in messages:
                        msg = await loop.run_in_executor(
                            None,
                            lambda m=message_info: self.service.users().messages().get(userId='me', id=m['id']).execute()
                        )
                        
                        # Extract sender
                        headers = msg.get('payload', {}).get('headers', [])
                        sender = next((h['value'] for h in headers if h['name'] == 'From'), "unknown")
                        
                        # Extract and decode text body
                        body_data = ""
                        payload = msg.get('payload', {})
                        if 'parts' in payload:
                            for part in payload['parts']:
                                if part['mimeType'] == 'text/plain':
                                    body_data = part.get('body', {}).get('data', '')
                                    break
                        else:
                            body_data = payload.get('body', {}).get('data', '')
                            
                        import base64
                        if body_data:
                            try:
                                text = base64.urlsafe_b64decode(body_data).decode('utf-8')
                            except Exception:
                                text = "Could not decode message."
                        else:
                            text = "Empty message."
                        
                        # Normalize payload
                        normalized_payload = {
                            "user_id": sender,
                            "session_id": sender,
                            "message": text,
                            "channel": "email"
                        }
                        
                        # POST to Agent Core (Layer 2)
                        print(f"Forwarding email from {sender} to Agent Core...")
                        try:
                            response = await client.post(self.agent_url, json=normalized_payload, timeout=30.0)
                            
                            if response.status_code == 200:
                                agent_data = response.json()
                                if agent_data.get("response"):
                                    await self.send_message(sender, agent_data["response"])
                            else:
                                print(f"Agent Core returned error {response.status_code}: {response.text}")
                        except Exception as e:
                            print(f"Failed to communicate with Agent Core: {e}")
                        
                        # Mark as read
                        await loop.run_in_executor(
                            None,
                            lambda m=message_info: self.service.users().messages().modify(
                                userId='me', id=m['id'],
                                body={'removeLabelIds': ['UNREAD']}
                            ).execute()
                        )
                
                await asyncio.sleep(10)
        except Exception as e:
            print(f"Error in Gmail Service listener: {e}")

email_handler_svc = EmailServiceHandler(agent_url=AGENT_CORE_URL)

@app.on_event("startup")
async def startup_event():
    # Start the polling loop in the background
    print("▶ Starting Email Polling Background Task...")
    asyncio.create_task(email_handler_svc.listen())

@app.post("/api/v1/send")
async def send_email(req: SendEmailRequest):
    """
    Endpoint for Layer 2 or others to trigger an outgoing email.
    """
    success = await email_handler_svc.send_message(req.recipient_id, req.message)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send email via Gmail API")
    return {"status": "sent"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
