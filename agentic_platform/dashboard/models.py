"""
Database schema definition models.
Defines typing or ORM equivalence for Supabase collections.
Tables: conversations, users, escalations, tool_logs, uploaded_documents
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass
class User:
    id: str
    email: Optional[str]
    telegram_id: Optional[str]
    created_at: datetime

@dataclass
class Conversation:
    id: str
    user_id: str
    status: str  # active, escalated, resolved
    created_at: datetime
    updated_at: datetime

@dataclass
class Escalation:
    id: str
    conversation_id: str
    reason: str
    assigned_to: Optional[str]
    status: str
    created_at: datetime

@dataclass
class ToolLog:
    id: str
    conversation_id: str
    tool_name: str
    parameters: Dict[str, Any]
    result: Dict[str, Any]
    executed_at: datetime

@dataclass
class UploadedDocument:
    id: str
    user_id: str
    file_url: str
    metadata: Dict[str, Any]
    uploaded_at: datetime
