from persistant_memory.loading_and_saving_chat import load_chat_history
import json

# def load_chat_conversation(session_id, last_n):
#     chat_data = load_chat_history(session_id=session_id, last_n=last_n)
#     if not chat_data["exists"]:
#         return ""

#     chat_history = ""
#     conversation = chat_data["conversation"]

#     for turn in conversation:
#         question = turn["question"]
#         raw_answer = turn["answer"]

#         # Handle string vs dictionary
#         if isinstance(raw_answer, str):
#             try:
#                 # Use LOADS (with an 's') for strings
#                 answer_data = json.loads(raw_answer)
#                 answer_text = answer_data.get("response", "")
#             except json.JSONDecodeError:
#                 # If it's just a plain string, use it directly
#                 answer_text = raw_answer
#         else:
#             # If it's already a dict
#             answer_text = raw_answer.get("response", "")

#         chat_history += f"question: {question}\nresponse: {answer_text}\n\n"

#     return chat_history


def load_chat_conversation(session_id, last_n=5):
    """
    Returns a formatted string of the last N turns.
    If it's a new session, it returns an empty string safely.
    """
    try:
        chat_data = load_chat_history(session_id=session_id, last_n=last_n)
    except Exception as e:
        print(f"⚠️ Warning: Could not load history for {session_id}: {e}")
        return ""

    if not chat_data or not chat_data.get("exists"):
        return ""

    formatted_history = ""
    conversation = chat_data.get("conversation", [])

    for turn in conversation:
        question = turn.get("question", "")
        raw_answer = turn.get("answer", "")

        # Extract 'response' text from the JSON/Dict answer
        if isinstance(raw_answer, dict):
            answer_text = raw_answer.get("response", "")
        elif isinstance(raw_answer, str):
            try:
                parsed = json.loads(raw_answer)
                answer_text = parsed.get("response", "")
            except:
                answer_text = raw_answer
        else:
            answer_text = str(raw_answer)

        formatted_history += f"User: {question}\nAI: {answer_text}\n\n"

    return formatted_history.strip()
           

def retrive_from_redis(cache_response):
    if cache_response.get("cache") is not None:
        print("🚀 CACHE HIT! Returning stored response from Redis.")
                
        raw_answer = cache_response["cache"]["answer"]

        # print("raw_answer", raw_answer)
            
        return raw_answer    
        
    else:
        return None