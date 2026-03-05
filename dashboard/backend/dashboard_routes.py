"""
Dashboard API Endpoints.
Provides backend-ready endpoints for the frontend application.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from knowledge_base_service import KnowledgeBaseService

router = APIRouter(prefix="/api/kb", tags=["Knowledge Base"])

class DocumentResponse(BaseModel):
    id: str
    name: str
    status: str
    chunk_count: int
    file_size_bytes: Optional[int]
    mime_type: Optional[str]
    uploaded_at: str
    processed_at: Optional[str]
    last_error: Optional[str]
    storage_path: Optional[str]

class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 5

# --- Global Reference for dependecy access ---
_kb_service: Optional['KnowledgeBaseService'] = None
_db_client = None

dashboard_router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

class DashboardRoutes:
    def __init__(self, kb_service: 'KnowledgeBaseService' = None, db_client=None):
        global _kb_service, _db_client
        _kb_service = kb_service
        _db_client = db_client
        if not _db_client:
            from shared.data_access.db_client import SupabaseClient
            _db_client = SupabaseClient().get_client()

    def register_routes(self, app):
        app.include_router(router)
        app.include_router(dashboard_router)

# --- Dashboard Route Implementations ---

@dashboard_router.get("/org")
async def get_org():
    res = _db_client.table("organizations").select("id").limit(1).execute()
    return res.data[0] if res.data else None

@dashboard_router.get("/stats/{org_id}")
async def get_dashboard_stats(org_id: str):
    # recent
    recent = _db_client.table("conversations").select("*, users(full_name, email), channels(type, display_name)").eq("organization_id", org_id).order("created_at", desc=True).limit(5).execute()
    # all
    all_convs = _db_client.table("conversations").select("status, tags, ai_confidence_score").eq("organization_id", org_id).execute()
    
    total = len(all_convs.data)
    resolved = len([c for c in all_convs.data if c.get("status") == "resolved"])
    escalated = len([c for c in all_convs.data if c.get("status") == "escalated"])
    active = len([c for c in all_convs.data if c.get("status") == "active"])
    
    tag_counts = {}
    for c in all_convs.data:
        for tag in c.get("tags") or []:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
    # Sample data fallback if no tags yet
    if not tag_counts:
        tag_counts = {"General Inquiry": 1, "Billing": 1, "Technical Support": 1, "Sales": 1}
            
    colors = ["hsl(24, 85%, 52%)", "hsl(38, 92%, 50%)", "hsl(0, 72%, 51%)", "hsl(217, 91%, 60%)", "hsl(142, 71%, 45%)"]
    intent_distribution = [{"name": k, "value": v, "fill": colors[i % len(colors)]} for i, (k, v) in enumerate(list(tag_counts.items())[:6])]
    
    return {
        "totalConversations": total,
        "resolvedCount": resolved,
        "escalatedCount": escalated,
        "activeCount": active,
        "autoResolvedPct": f"{(resolved/total*100):.1f}%" if total > 0 else "0%",
        "escalationRatePct": f"{(escalated/total*100):.1f}%" if total > 0 else "0%",
        "recentConversations": recent.data,
        "intentDistribution": intent_distribution
    }

@dashboard_router.get("/conversations/{org_id}")
async def get_conversations(org_id: str):
    res = _db_client.table("conversations").select("*, users(full_name, email), channels(type, display_name)").eq("organization_id", org_id).order("created_at", desc=True).execute()
    return res.data

@dashboard_router.get("/usage/{org_id}")
async def get_usage(org_id: str, days_back: int = 30):
    from datetime import datetime, timedelta
    since = (datetime.utcnow() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    res = _db_client.table("organization_usage_daily").select("usage_date,conversations_count,escalations_count,messages_count,tool_calls_count,ai_message_count").eq("organization_id", org_id).gte("usage_date", since).order("usage_date").execute()
    return res.data

@dashboard_router.get("/channels/{org_id}")
async def get_channels(org_id: str):
    res = _db_client.table("channels").select("id,type,display_name,status,last_active_at").eq("organization_id", org_id).order("type").execute()
    return res.data

@dashboard_router.get("/reminders/{org_id}")
async def get_reminders(org_id: str):
    res = _db_client.table("reminders").select("*").eq("organization_id", org_id).order("created_at", desc=True).execute()
    return res.data

class ReminderCreate(BaseModel):
    organization_id: str
    type: str
    title: str
    description: Optional[str] = None
    link: Optional[str] = None

@dashboard_router.post("/reminders")
async def create_reminder(req: ReminderCreate):
    res = _db_client.table("reminders").insert(req.dict()).execute()
    return res.data

@dashboard_router.put("/reminders/{reminder_id}/read")
async def mark_reminder_read(reminder_id: str):
    res = _db_client.table("reminders").update({"is_read": True}).eq("id", reminder_id).execute()
    return res.data

@dashboard_router.put("/reminders/org/{org_id}/read-all")
async def mark_all_reminders_read(org_id: str):
    res = _db_client.table("reminders").update({"is_read": True}).eq("organization_id", org_id).eq("is_read", False).execute()
    return res.data

@dashboard_router.delete("/reminders/org/{org_id}")
async def clear_reminders(org_id: str):
    res = _db_client.table("reminders").delete().eq("organization_id", org_id).execute()
    return res.data

@dashboard_router.get("/cases/{case_id}")
async def get_case_detail(case_id: str):
    res = _db_client.table("conversations").select("*, users(full_name, email), channels(type, display_name), messages!session_id(*)").eq("id", case_id).execute()
    if res.data:
        conv = res.data[0]
        if conv.get("messages"):
            conv["messages"].sort(key=lambda x: x["created_at"])
        return conv
    raise HTTPException(status_code=404, detail="Case not found")

# --- Channel Connect/Disconnect Endpoints ---

class ChannelConnectRequest(BaseModel):
    organization_id: str
    type: str  # gmail, telegram, whatsapp, webchat, phone
    display_name: Optional[str] = None
    config: Optional[dict] = None  # channel-specific config (bot token, credentials path, etc.)

@dashboard_router.post("/channels/connect")
async def connect_channel(req: ChannelConnectRequest):
    """
    Connect a channel: validate credentials/config, then register in DB.
    """
    import os
    from datetime import datetime

    # Channel-specific validation
    if req.type == "gmail":
        # Check if credentials.json exists (OAuth app configured)
        from pathlib import Path
        _proj_root = Path(__file__).resolve().parent.parent.parent
        creds_path = req.config.get("credentials_path", os.getenv("GMAIL_CREDENTIALS_PATH", "secrets/credentials.json")) if req.config else os.getenv("GMAIL_CREDENTIALS_PATH", "secrets/credentials.json")
        token_path = req.config.get("token_path", os.getenv("GMAIL_TOKEN_PATH", "secrets/token.json")) if req.config else os.getenv("GMAIL_TOKEN_PATH", "secrets/token.json")

        # Resolve to absolute paths relative to project root
        if not Path(creds_path).is_absolute():
            creds_path = str(_proj_root / creds_path)
        if not Path(token_path).is_absolute():
            token_path = str(_proj_root / token_path)

        if not os.path.exists(creds_path):
            raise HTTPException(
                status_code=400,
                detail=f"Gmail OAuth credentials file not found at '{creds_path}'. Download it from Google Cloud Console and place it in the 'secrets/' directory."
            )

        # If token.json doesn't exist, we need to trigger OAuth flow (one-time)
        if not os.path.exists(token_path):
            try:
                from google_auth_oauthlib.flow import InstalledAppFlow
                SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                creds = flow.run_local_server(
                    port=0,
                    access_type='offline',
                    prompt='consent',
                )
                os.makedirs(os.path.dirname(token_path), exist_ok=True)
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Gmail OAuth flow failed: {str(e)}")

    elif req.type == "telegram":
        bot_token = (req.config or {}).get("bot_token") or os.getenv("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            raise HTTPException(
                status_code=400,
                detail="Telegram Bot Token is required. Provide it in config or set TELEGRAM_BOT_TOKEN env var."
            )

    # Upsert channel row in DB
    channel_data = {
        "organization_id": req.organization_id,
        "type": req.type,
        "display_name": req.display_name or req.type.capitalize(),
        "status": "active",
        "last_active_at": datetime.utcnow().isoformat(),
    }

    res = _db_client.table("channels").upsert(
        channel_data,
        on_conflict="organization_id,type"
    ).execute()

    return {"status": "connected", "channel": res.data}

@dashboard_router.delete("/channels/{channel_id}/disconnect")
async def disconnect_channel(channel_id: str):
    """
    Disconnect a channel: set status to inactive or delete the row.
    If it's Gmail, also delete the token.json file so the background
    service stops polling and a new OAuth flow is required on next connect.
    """
    import os
    from pathlib import Path
    
    # Check what type of channel we are disconnecting
    channel_query = _db_client.table("channels").select("type").eq("id", channel_id).execute()
    if not channel_query.data:
        raise HTTPException(status_code=404, detail="Channel not found")
        
    channel_type = channel_query.data[0].get("type")

    # Set status to inactive in DB
    res = _db_client.table("channels").update({"status": "inactive"}).eq("id", channel_id).execute()
    
    # If it's gmail, delete the associated token file
    if channel_type == "gmail":
        _proj_root = Path(__file__).resolve().parent.parent.parent
        token_path = os.getenv("GMAIL_TOKEN_PATH", "secrets/token.json")
        if not Path(token_path).is_absolute():
            token_path = str(_proj_root / token_path)
            
        if os.path.exists(token_path):
            try:
                os.remove(token_path)
                print(f"Deleted Gmail token file at {token_path}")
            except Exception as e:
                print(f"Failed to delete Gmail token file: {e}")

    return {"status": "disconnected"}

# --- KB Route Implementations ---

@router.get("/files", response_model=List[DocumentResponse])
async def get_files():
    if not _kb_service:
        raise HTTPException(status_code=500, detail="KB Service not initialized")
    org_id = _kb_service.get_default_org_id()
    res = _kb_service.get_documents(org_id)
    return res.data

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not _kb_service:
        raise HTTPException(status_code=500, detail="KB Service not initialized")
    org_id = _kb_service.get_default_org_id()
    content = await file.read()
    try:
        doc_id = await _kb_service.ingest_document(org_id, file.filename, content)
        return {"id": doc_id, "status": "processing"}
    except Exception as e:
        print(f"API ERROR in /upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_stats():
    if not _kb_service:
        raise HTTPException(status_code=500, detail="KB Service not initialized")
    org_id = _kb_service.get_default_org_id()
    return _kb_service.get_kb_stats(org_id)

@router.post("/search")
async def search_kb(req: SearchRequest):
    if not _kb_service:
        raise HTTPException(status_code=500, detail="KB Service not initialized")
    org_id = _kb_service.get_default_org_id()
    return await _kb_service.search_knowledge_base(org_id, req.query, req.limit)

@router.get("/view/{file_id}")
async def view_file(file_id: str):
    if not _kb_service:
        raise HTTPException(status_code=500, detail="KB Service not initialized")
    res = _kb_service.get_document_by_id(file_id)
    if not res.data:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc = res.data
    if not doc.get("storage_path"):
        raise HTTPException(status_code=400, detail="Document has no storage path")

    try:
        # Generate a signed URL for 1 hour
        signed = _kb_service.db.storage.from_(_kb_service.bucket_name).create_signed_url(
            path=doc["storage_path"],
            expires_in=3600
        )
        print("SIGNED DEBUG:", signed)

        url = None
        # Handle cases where `signed` is a dict with 'signedURL' or 'signedUrl'
        if isinstance(signed, dict):
            url = signed.get("signedURL") or signed.get("signedUrl")
        # Handle cases where `signed` is a string (older clients or direct result)
        elif isinstance(signed, str):
            url = signed
        # Handle cases where the result has a .signed_url attribute (newer python clients)
        elif hasattr(signed, 'signed_url'):
             url = signed.signed_url
        elif hasattr(signed, 'signedURL'):
             url = signed.signedURL

        if not url:
            raise Exception(f"Could not extract signed URL from response type {type(signed)}: {signed}")

        return {"url": url}
    except Exception as e:
        print(f"SIGNED URL ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")

@router.delete("/files/{file_id}")
async def delete_file(file_id: str):
    if not _kb_service:
        raise HTTPException(status_code=500, detail="KB Service not initialized")
    _kb_service.delete_document(file_id)
    return {"status": "deleted"}
