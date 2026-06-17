from pydantic import BaseModel
from typing import Optional, List, Dict


class SessionCreate(BaseModel):
    title: Optional[str] = "New Chat"

class ChatMessageCreate(BaseModel):
    session_id: str
    role: str                 # "user" or "assistant"
    response: str

    # Bot-only optional fields
    bold_words: Optional[List[str]] = None
    meta_data: Optional[List[Dict]] = None
    follow_up: Optional[str] = None
    table_data: Optional[List[str]] = None
    ucid: Optional[str] = None

    class Config:
        orm_mode = True