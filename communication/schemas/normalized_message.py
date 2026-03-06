from typing import Dict, Any
from pydantic import BaseModel

class NormalizedMessage(BaseModel):
    user_id: str
    session_id: str
    message: str
    channel: str
    metadata: Dict[str, Any] = {}
