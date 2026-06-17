from fastapi import FastAPI, Depends ,HTTPException
from sqlalchemy.orm import Session
from database import Base, engine, get_db
from models import ChatSession, ChatMessage
from schemas import SessionCreate, ChatMessageCreate
import json
from helpers import get_all_chats_by_session , get_all_sessions_with_first_message

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Offline Chatbot API")

# ---------------------
# Create new chat session
# ---------------------
@app.post("/chat/session")
def create_session(payload: SessionCreate, db: Session = Depends(get_db)):
    session = ChatSession(title=payload.title)
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"session_id": session.id, "title": session.title}


# ---------------------
# Save user or bot message
# ---------------------
@app.post("/chat/message")
def store_chat_message(payload: ChatMessageCreate, db: Session = Depends(get_db)):
    # Convert lists/dicts to JSON strings if present
    msg = ChatMessage(
        session_id=payload.session_id,
        role=payload.role,
        message=payload.message,
        bold_words=json.dumps(payload.bold_words) if payload.bold_words else None,
        meta_data=json.dumps(payload.meta_data) if payload.meta_data else None,
        follow_up=payload.follow_up,
        table_data=json.dumps(payload.table_data) if payload.table_data else None,
        ucid=payload.ucid
    )

    db.add(msg)
    db.commit()
    db.refresh(msg)

    return {"status": "success", "message_id": msg.id}

# ---------------------
# Get all messages for a session
# ---------------------
@app.get("/sessions/{session_id}/chats")
def get_chats(session_id: str, db: Session = Depends(get_db)):
    chats = get_all_chats_by_session(db, session_id)

    if not chats:
        raise HTTPException(status_code=404, detail="No chats found for this session")

    return {
        "session_id": session_id,
        "total_messages": len(chats),
        "chats": chats
    }

# ---------------------
# Get  session list
# ---------------------

@app.get("/sessions")
def list_sessions(db: Session = Depends(get_db)):
    sessions = get_all_sessions_with_first_message(db)

    return {
        "total_sessions": len(sessions),
        "sessions": sessions
    }