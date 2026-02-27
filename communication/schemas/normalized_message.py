from dataclasses import dataclass

@dataclass
class NormalizedMessage:
    user_id: str
    session_id: str
    message: str
    channel: str