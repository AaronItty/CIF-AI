"""
Email integration handler via Gmail API.
Stateless handler that normalizes input and passes it to Agent Core.
"""

import os
import base64
import asyncio
from email.message import EmailMessage
from typing import Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from shared.interfaces import BaseChannelHandler, AgentInterface
from communication.schemas.normalized_message import NormalizedMessage

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

class EmailHandler(BaseChannelHandler):
    """
    Handles Email interactions using the Gmail API.
    """
    
    def __init__(self, agent: AgentInterface, gmail_settings: Dict[str, Any] = None):
        self.agent = agent
        self.gmail_settings = gmail_settings or {}
        self.credentials_path = self.gmail_settings.get('credentials_path', 'credentials.json')
        self.token_path = self.gmail_settings.get('token_path', 'token.json')
        self.service = None
        
    def _authenticate(self):
        """Authenticate and return the Gmail API service."""
        creds = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            elif os.path.exists(self.credentials_path):
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            else:
                print(f"Warning: neither {self.token_path} nor {self.credentials_path} found. Gmail API skipping auth.")
                return None
                
            # Save the credentials for the next run
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())

        try:
            return build('gmail', 'v1', credentials=creds)
        except Exception as e:
            print(f"Failed to build Gmail service: {e}")
            return None
            
    async def listen(self):
        """
        Start Gmail API listener (polling method).
        """
        if not self.service:
            self.service = self._authenticate()
            
        if not self.service:
            print("Gmail API authentication failed. Listener stopping.")
            return

        print("Started Gmail API listener...")
        try:
            while True:
                # Poll for unread messages using run_in_executor to not block event loop
                loop = asyncio.get_event_loop()
                results = await loop.run_in_executor(
                    None, 
                    lambda: self.service.users().messages().list(userId='me', q='is:unread').execute()
                )
                
                messages = results.get('messages', [])
                
                for message_info in messages:
                    msg = await loop.run_in_executor(
                        None,
                        lambda m=message_info: self.service.users().messages().get(userId='me', id=m['id']).execute()
                    )
                    
                    print(f"Received new email with ID: {message_info['id']}")
                    
                    # Extract sender
                    headers = msg.get('payload', {}).get('headers', [])
                    sender = "unknown"
                    for header in headers:
                        if header['name'] == 'From':
                            sender = header['value']
                            break
                            
                    # Extract text body
                    body_data = ""
                    payload = msg.get('payload', {})
                    if 'parts' in payload:
                        for part in payload['parts']:
                            if part['mimeType'] == 'text/plain':
                                body_data = part.get('body', {}).get('data', '')
                                break
                    else:
                        body_data = payload.get('body', {}).get('data', '')
                        
                    if body_data:
                        try:
                            # Gmail API sends base64url encoded data
                            text = base64.urlsafe_b64decode(body_data).decode('utf-8')
                        except Exception:
                            text = "Could not decode message."
                    else:
                        text = "Empty message."
                        
                    # Normalize and pass to agent
                    normalized = NormalizedMessage(
                        user_id=sender,
                        session_id=sender,
                        message=text,
                        channel="email"
                    )
                    
                    response = await self.agent.process_message(normalized)
                    
                    if response and response.get("text"):
                        await self.send_message(normalized.session_id, response["text"])
                    
                    # Remove UNREAD label to prevent processing again
                    await loop.run_in_executor(
                        None,
                        lambda m=message_info: self.service.users().messages().modify(
                            userId='me', id=m['id'],
                            body={'removeLabelIds': ['UNREAD']}
                        ).execute()
                    )
                
                await asyncio.sleep(10) # Poll every 10 seconds
        except Exception as e:
            print(f"Error in Gmail listener: {e}")
            
    async def send_message(self, recipient_id: str, message: str) -> bool:
        """
        Send an email response using the Gmail API.
        """
        if not self.service:
            self.service = self._authenticate()
            if not self.service:
                print("Gmail API authentication failed. Cannot send message.")
                return False

        try:
            email_msg = EmailMessage()
            email_msg.set_content(message)
            email_msg['To'] = recipient_id
            email_msg['From'] = 'me'
            email_msg['Subject'] = 'Agent Response'

            encoded_message = base64.urlsafe_b64encode(email_msg.as_bytes()).decode()

            create_message = {
                'raw': encoded_message
            }

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.service.users().messages().send(userId="me", body=create_message).execute()
            )
            return True
            
        except HttpError as error:
            print(f"An error occurred sending email: {error}")
            return False
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
