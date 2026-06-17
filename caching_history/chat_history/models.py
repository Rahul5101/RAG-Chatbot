from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime
from caching_history.chat_history.database import Base
import uuid

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(
        String(32),
        primary_key=True,
        default=lambda: uuid.uuid4().hex,
        index=True
    )
    title = Column(String, default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    session_id = Column(String(32))   # links to ChatSession
    role = Column(String)             # "user" or "assistant"
    response = Column(Text)
    bold_words = Column(Text, nullable=True)  
    meta_data = Column(Text, nullable=True)
    follow_up = Column(Text, nullable=True)
    table_data = Column(Text, nullable=True)
    ucid = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ChatMessage id={self.id} session_id={self.session_id} role={self.role} message={self.message}>"