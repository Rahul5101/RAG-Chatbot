from sqlalchemy.orm import Session
from caching_history.chat_history.models import ChatMessage
import json
from sqlalchemy import func
 

def get_all_sessions_with_first_message(db: Session):
    subquery = (
        db.query(
            ChatMessage.session_id,
            func.min(ChatMessage.created_at).label("first_time")
        )
        .group_by(ChatMessage.session_id)
        .subquery()
    )

    result = (
        db.query(ChatMessage)
        .join(
            subquery,
            (ChatMessage.session_id == subquery.c.session_id) &
            (ChatMessage.created_at == subquery.c.first_time)
        )
        .filter(ChatMessage.role == "user")
        .order_by(ChatMessage.created_at.desc())
        .all()
    )

    return [
        {
            "session_id": row.session_id,
            "title": row.response,
            "created_at": row.created_at
        }
        for row in result
    ]


def get_all_chats_by_session(db: Session, session_id: str):
    chats = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    return [
        {
            "id": chat.id,
            "role": chat.role,
            "response": chat.response,
            "bold_words": json.loads(chat.bold_words) if chat.bold_words else [],
            "meta_data": json.loads(chat.meta_data) if chat.meta_data else [],
            "follow_up": chat.follow_up,
            "table_data": json.loads(chat.table_data) if chat.table_data else [],
            "ucid": chat.ucid,
            "created_at": chat.created_at,
        }
        for chat in chats
    ]
