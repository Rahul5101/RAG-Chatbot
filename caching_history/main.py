from fastapi import FastAPI
from pydantic import BaseModel
import asyncio
from fastapi.responses import JSONResponse
import time
from src.step_3_llm_loaders import main
from workflow_milvus import process_folder
# from milvus_database.milvus_loading import loading_milvus
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Header
from pathlib import Path
from urllib.parse import unquote,quote
from fastapi.responses import FileResponse

from data_cleaning.markdown_cleaning import process_all_files
from drop_collection import drop_collection_from_milvus

BASE_DIR = os.getcwd()
app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000",
    "https://km-income-tax-dot-knowledge-minor.el.r.appspot.com/",
    "*",  # Use "*" to allow all origins (not recommended in production)
]
# Add CORS middleware to your app
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # List of allowed origins
    allow_credentials=True,           # Allow cookies and auth headers
    allow_methods=["*"],              # Allow all HTTP methods
    allow_headers=["*"],              # Allow all headers
)


# Request model: user sends a question
class QuestionRequest(BaseModel):
    question: str
    answer_type: str
    session_id: str
# # Response model: we respond with JSON
class AnswerResponse(BaseModel):
    answer: str

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/query_old", response_model=AnswerResponse)
def answer_question(request: QuestionRequest):
    user_question = request.question
    start_time = time.time()

    # db_load = loading_milvus()
    response_data = asyncio.run(main(query=user_question))
    elapsed_time = time.time() - start_time

    print(f"\nTotal time consumed: {elapsed_time:.2f} seconds")

    return JSONResponse(response_data)



class FolderPathRequest(BaseModel):
    folder_path: str

@app.post("/data_ingestion")
def data_ingestion_into_milvus(request: FolderPathRequest):
    """
    Accepts a folder path, processes all files in it,
    and inserts data into Milvus.
    """
    input_folder = os.getenv("markdown_input_folder")
    output_folder = os.getenv("markdown_output_folder")

    if not input_folder:
        raise ValueError("❌ Environment variable 'markdown_input_folder' not set.")

    if not output_folder:
        raise ValueError("❌ Environment variable 'markdown_output_folder' not set.")

    print(f"📥 Input Folder: {input_folder}")
    print(f"📤 Output Folder: {output_folder}")

    process_all_files(input_folder, output_folder)
    print("Done!")

    folder_path = request.folder_path

    if not os.path.exists(folder_path):
        return JSONResponse(
            status_code=400,
            content={"error": f"Folder path '{folder_path}' does not exist."}
        )

    try:
        process_folder(root_folder=folder_path)
        return JSONResponse(
            content={"message": f"Data ingestion completed successfully for folder: {folder_path}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to ingest data: {str(e)}"}
        )


@app.get("/drop")
def data_drop_from_milvus():
    drop_collection_from_milvus()

    return {"message": "collection dropped"}



from fastapi import FastAPI
from fastapi.responses import FileResponse
from urllib.parse import unquote
import os

@app.get("/open-pdf")
async def open_pdf(file_path: str):
    decoded_path = unquote(file_path)
    clean_path = os.path.normpath(decoded_path)

    print("Trying to open:", clean_path)

    if not os.path.exists(clean_path):
        return {"error": f"File not found: {clean_path}"}

    return FileResponse(
        clean_path,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename={os.path.basename(clean_path)}"
        }
    )






import typing as t
from caching.redis_semantic_cache import cache_rag,upsert_rag_response,simple_id_generator
from fastapi import FastAPI, Query
DEFAULT_K = 1
from caching.redis_semantic_cache import create_index_if_not_exists
DIM = os.getenv("DIM",1024)   
idgen = simple_id_generator() 

# @app.post("/query", response_model=AnswerResponse)
# def answer_question(request: QuestionRequest):
#     user_question = request.question
#     answer_type = request.answer_type
#     create_index_if_not_exists(DIM)
#     print("answer type: ",answer_type)

#     if answer_type != "deepthink":
#         response_data = cache_rag(user_question,DEFAULT_K)

#         print("response data: ",response_data)

#         if response_data['cache'] is not None:
#             print("inside cashing-----------------------------------------------------------------------------")
#             return JSONResponse(response_data["cache"]['answer'])
#         response_data = asyncio.run(main(query=user_question))
#         print("getting rag without caching-----------------------------------------------------------------------------")

#         upsert_rag_response(rag_answer=response_data,query_text=user_question,id_generator=idgen)
#         print("rag added data")
#         return JSONResponse(response_data)
    
#     elif answer_type == "deepthink":
#         response_data = asyncio.run(main(query=user_question))
#         print("deep thinking mode------------------------------------------------------------")
#         return JSONResponse(response_data)


        


from fastapi import FastAPI, Depends ,HTTPException
from sqlalchemy.orm import Session
from chat_history.database import Base, engine, get_db
from chat_history.models import ChatSession, ChatMessage
from chat_history.schemas import SessionCreate, ChatMessageCreate
import json
from chat_history.helpers import get_all_chats_by_session , get_all_sessions_with_first_message
from src.step_8_session_history import get_recent_history
# from src.step_5_prompt import build_conversation_prompt
from sqlalchemy.orm import Session

# Create tables
Base.metadata.create_all(bind=engine)

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
    # print("payload: ",payload)
    msg = ChatMessage(
        session_id=payload.session_id,
        role=payload.role,
        response=payload.response,
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






@app.post("/query", response_model=AnswerResponse)
def answer_question(request: QuestionRequest, db: Session = Depends(get_db)):
    user_question = request.question
    answer_type = request.answer_type
    session_id = request.session_id
    print("answer type: ",answer_type)

    create_index_if_not_exists(DIM)
    # ----------------------------
    # ✅ SAVE USER MESSAGE FIRST
    # ----------------------------
    # user_msg = ChatMessage(
    #     session_id=session_id,
    #     role="user",
    #     response=user_question
    # )
    # db.add(user_msg)
    # db.commit()

    # ----------------------------
    # STEP-1: Fetch chat history
    # ----------------------------
    history = get_recent_history(db, session_id)

    print("history: ",history)

    # ----------------------------
    # STEP-2: Build prompt
    # ----------------------------
    # prompt = build_conversation_prompt(history, user_question)

    # print("Builder prompt: : ",prompt)

    # ----------------------------
    # STEP-3: Run RAG with prompt
    # ----------------------------
    if answer_type != "deepthink":

        cache_result = cache_rag(user_question, DEFAULT_K)

        if cache_result["cache"] is not None:
            answer = cache_result["cache"]["answer"]

        else:
            answer = asyncio.run(main(query=user_question,history=history))
            upsert_rag_response(
                rag_answer=answer,
                query_text=user_question,
                id_generator=idgen
            )

    else:
        answer = asyncio.run(main(query=user_question,history=history))

    # ----------------------------
    # Normalize LLM response
    # ----------------------------
    # if isinstance(answer, dict):
    #     # print("answer inside: ",answer)
    #     answer_text = answer.get("response")
    #     if not answer_text:
    #         raise ValueError("LLM response missing 'response' field")

    #     bold_words = answer.get("bold_words")
    #     meta_data = answer.get("meta_data")
    #     follow_up = answer.get("follow_up")
    #     table_data = answer.get("table_data")
    #     ucid = answer.get("ucid")
    # else:
    #     answer_text = str(answer)
    #     bold_words = meta_data = follow_up = table_data = ucid = None


#     bot_msg = ChatMessage(
#     session_id=session_id,
#     role="assistant",
#     message=answer_text,  # ✅ REAL ANSWER TEXT
#     bold_words=json.dumps(bold_words) if bold_words else None,
#     meta_data=json.dumps(meta_data) if meta_data else None,
#     follow_up=follow_up,
#     table_data=json.dumps(table_data) if table_data else None,
#     ucid=ucid
# )

#     db.add(bot_msg)
#     db.commit()

    return JSONResponse(answer)

