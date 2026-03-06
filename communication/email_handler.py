"""
Email integration handler via Gmail API.
Stateless handler that normalizes input and passes it to Agent Core.

Security notes:
  - credentials.json and token.json are gitignored and must NEVER be committed.
  - Paths are resolved from environment variables (GMAIL_CREDENTIALS_PATH, GMAIL_TOKEN_PATH)
    and converted to absolute paths relative to the project root.
  - OAuth uses access_type='offline' to obtain a long-lived refresh token,
    so re-authentication is only needed if the token file is deleted or scopes change.
"""

import os
import base64
import asyncio
from pathlib import Path
from email.message import EmailMessage
from typing import Dict, Any

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from shared.interfaces import BaseChannelHandler, AgentInterface
from communication.schemas.normalized_message import NormalizedMessage

load_dotenv()

# Project root = parent of the 'communication' package directory
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

class EmailHandler(BaseChannelHandler):
    """
    Handles Email interactions using the Gmail API.
    """
    
    def __init__(self, agent: AgentInterface, gmail_settings: Dict[str, Any] = None):
        self.agent = agent
        self.gmail_settings = gmail_settings or {}

        # Resolve credential paths: settings dict > env var > default
        raw_creds = self.gmail_settings.get(
            'credentials_path',
            os.getenv('GMAIL_CREDENTIALS_PATH', 'secrets/credentials.json')
        )
        raw_token = self.gmail_settings.get(
            'token_path',
            os.getenv('GMAIL_TOKEN_PATH', 'secrets/token.json')
        )

        # Make paths absolute (relative to project root)
        self.credentials_path = str(
            Path(raw_creds) if Path(raw_creds).is_absolute() else _PROJECT_ROOT / raw_creds
        )
        self.token_path = str(
            Path(raw_token) if Path(raw_token).is_absolute() else _PROJECT_ROOT / raw_token
        )

        self.service = None
        
    def _authenticate(self):
        """
        Authenticate and return the Gmail API service.

        Flow:
          1. Try loading an existing token from token_path.
          2. If the token is expired but has a refresh_token, silently refresh it.
          3. Only if no usable token exists, start the interactive OAuth flow
             (one-time operation — the resulting refresh token is saved).
        """
        creds = None

        # --- Step 1: Try to load a saved token ---
        if os.path.exists(self.token_path):
            try:
                creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
                print(f"[Gmail Auth] Loaded existing token from {self.token_path}")
            except Exception as e:
                print(f"[Gmail Auth] Failed to load token file: {e}")
                creds = None

        # --- Step 2: Refresh or re-authenticate ---
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    print("[Gmail Auth] Token refreshed successfully (no user interaction needed).")
                except Exception as e:
                    print(f"[Gmail Auth] Token refresh failed: {e}. Will need re-authentication.")
                    creds = None

            if not creds or not creds.valid:
                print(f"[Gmail Auth] No valid token found. Please connect the Gmail channel via the Dashboard UI.")
                return None

            # --- Save token for future runs (if it was refreshed) ---
            os.makedirs(os.path.dirname(self.token_path), exist_ok=True)
            with open(self.token_path, 'w') as token_file:
                token_file.write(creds.to_json())

        try:
            return build('gmail', 'v1', credentials=creds)
        except Exception as e:
            print(f"[Gmail Auth] Failed to build Gmail service: {e}")
            return None
            
    async def listen(self):
        """
        Start Gmail API listener (polling method).
        """
        print("Started Gmail API listener...")
        try:
            while True:
                if not self.service:
                    self.service = self._authenticate()
                    
                if not self.service:
                    print("[Gmail API] Not connected. Waiting for OAuth via Dashboard... (retrying in 10s)")
                    await asyncio.sleep(10)
                    continue

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
                    
                    # Extract sender and headers
                    headers = msg.get('payload', {}).get('headers', [])
                    sender = "unknown"
                    subject = "Agent Response"
                    message_id = None
                    for header in headers:
                        if header['name'] == 'From':
                            sender = header['value']
                        elif header['name'] == 'Subject':
                            subject = header['value']
                        elif header['name'] == 'Message-ID':
                            message_id = header['value']
                            
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
                        channel="email",
                        metadata={
                            "subject": subject,
                            "message_id": message_id
                        }
                    )
                    
                    response = await self.agent.process_message(normalized)
                    
                    if response and response.get("text"):
                        await self.send_message(
                            normalized.session_id, 
                            response["text"], 
                            metadata=normalized.metadata
                        )
                    
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
            
    async def send_message(self, recipient_id: str, message: str, subject: str = "Agent Response", metadata: dict = None) -> bool:
        """
        Send an email response using the Gmail API.
        If metadata is provided with message_id and original subject, reply directly to the thread.
        """
        metadata = metadata or {}
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
            
            orig_msg_id = metadata.get('message_id')
            orig_subject = metadata.get('subject')

            if orig_msg_id and orig_subject:
                # Format to Re: if not already present
                if not orig_subject.lower().startswith("re:"):
                    email_msg['Subject'] = f"Re: {orig_subject}"
                else:
                    email_msg['Subject'] = orig_subject
                    
                email_msg['In-Reply-To'] = orig_msg_id
                email_msg['References'] = orig_msg_id
            else:
                 email_msg['Subject'] = subject

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
