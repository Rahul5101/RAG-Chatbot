# from models import ChatMessage
from caching_history.chat_history.models import ChatMessage

def get_recent_history(db, session_id, limit=6):
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .all()
    )

    messages.reverse()

    history = []
    for m in messages:
        if m.response:
            history.append({"role": m.role, "content": m.response})

    return history
