import os
import json
import re
import time
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.output_parsers import StrOutputParser
from multilingual_pipeline.conversion import output_converison
from src.step_4_processing import process_file
from src.utils import load_config
from multilingual_pipeline.conversion import output_converison
# from url_integration.gcs_url import generate_signed_url
from src.step_7_utility import escape_inner_quotes, replace_links
from persistant_memory.loading_and_saving_chat import save_chat_turn, init_db,get_unique_query_count,search_history_semantic
from caching_history.caching.redis_semantic_cache import upsert_rag_response,simple_id_generator,cache_rag,create_index_if_not_exists,refresh_redis_from_sqlite
from persistant_memory.load_chat_history import retrive_from_redis
from caching_history.chat_history.models import ChatMessage
from sqlalchemy.orm import Session
from src.step_8_session_history import get_recent_history
# from persistant_memory.load_chat_history import load_chat_conversation
from url_integration.gcs_url import generate_signed_url

DB_PATH = "chat_history.db"
import sqlite3              
init_db()
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
K_THRESHOLD = 17
load_dotenv()       
id_gen = simple_id_generator()
create_index_if_not_exists()
# Legal document generator

load_dotenv()

def parse_rag_json_response(response_text: str):
    cleaned = (response_text or "").strip()
    if not cleaned:
        return None

    fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL | re.IGNORECASE)
    if fence_match:
        cleaned = fence_match.group(1).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(cleaned[start:end + 1])
            except json.JSONDecodeError:
                return None
    return None

def build_fallback_output(response_text: str, metadata=None):
    fallback_text = (response_text or "").strip()
    if not fallback_text:
        fallback_text = (
            "I could not generate a structured answer for this question from the retrieved documents. "
            "Please try rephrasing the question or use normal mode."
        )

    return {
        "bold_words": list(set(re.findall(r"\*\*(.*?)\*\*", fallback_text))),
        "meta_data": metadata or [],
        "response": fallback_text,
        "follow_up": "Can you rephrase the question with more details?",
        "table_data": [],
        "confidence_score": 0,
        "ucid": "99_18"
    }, 0

def update_url(metadata): 
    updated_metadata = []
    for item in metadata:
        pageno = item.get("page")
        source = item.get("source")
        encoded_source = source.replace(" ", "%20")
        temp_url = f"https://storage.cloud.google.com/km-navi-mdl-data/{encoded_source}.pdf"
        signed_url = generate_signed_url(gcs_url=temp_url)
        signed_url_with_page = f"{signed_url}#page={pageno}"
        
        item["signed_url"] = signed_url_with_page
        
    return metadata

def deepthink_pipeline(query:str,db:Session,detected_lang="en",session_id="deafult_session"):
    config = load_config()
    em_model_name = config['embedding']['google']['model_name']
    embedding_model = GoogleGenerativeAIEmbeddings(model=em_model_name)
    chat_history = get_recent_history(db, session_id=session_id, limit=3)  
    # print("chat_history: ",chat_history)
    tasks = process_file(
        query=query,
        embedding_model=embedding_model,
        chat_history = chat_history
    )
        
    results=[tasks]
    per_file_responses = [r for r in results if r]
    if not per_file_responses:
        return build_fallback_output("")

    # Step 2: Filter irrelevant responses
    irrelevant_pattern = re.compile(r"(does not provide relevant information|answer is not available)", re.IGNORECASE)
        
        # Step 3: Deduplicate metadata
    all_meta_data = []
    seen_files_pages = set()
    for r in per_file_responses:
        all_meta_data.extend(r["metadata"])

    
    complete_response = "\n\n".join([r["response"] for r in per_file_responses])

    print("complete response: ",complete_response)
    bold_words = list(set(re.findall(r"\*\*(.*?)\*\*", complete_response)))

        # Step 5: Replace links and escape quotes
        # html_text = replace_links(complete_response, all_meta_data)
        # clean_output = escape_inner_quotes(html_text.strip())

        # Convert to dict (your JSON format)
    translated_output = parse_rag_json_response(complete_response)
    if not translated_output:
        print("Could not parse RAG JSON response. Returning fallback response.")
        return build_fallback_output(complete_response, all_meta_data)

    explanation_and_summary = f"{translated_output.get('Explanation')}\n\n**Summary:**\n{translated_output.get('Summary')}"
    confidence_score = translated_output.get("Confidence_Score")
    follow_up_question = translated_output.get("Follow_up")
    table_data = translated_output.get("table_data")

    # Step 6: Translation
    if detected_lang not in ["en", "hi", "mr", "te"]:
        detected_lang = "en"


    explanation_translated = output_converison(explanation_and_summary, detected_lang)
    follow_up_translated = output_converison(follow_up_question, detected_lang)
    table_data_translated = output_converison(table_data, detected_lang)

        # Step 7: Final output dict
    output = {
        "bold_words": bold_words,
        "meta_data": all_meta_data,
        "response":  explanation_translated ,
        "follow_up": follow_up_translated,
        "table_data": [table_data_translated],
        "confidence_score": confidence_score,
        "ucid": "99_18"  # example unique ID
    }
    print("Final output prepared.", output)
        
        
    return output, confidence_score
    



async def main(query: str,db:Session, detected_lang: str = "en",session_id = "defaut_session", answer_type :str="normal"):

    print("Loading embedding model and LLM...")

    # Load model configuration
    config = load_config()
    em_model_name = config['embedding']['google']['model_name']
    embedding_model = GoogleGenerativeAIEmbeddings(model=em_model_name)
    query_vector = embedding_model.embed_query(query)

    print(f"\n[1] Checking Cache for Query: {query}")
        
    if answer_type != "deepthink":
        #first query goes into the redis 
        try:
            cache_lookup = cache_rag(query, query_vector)
            cache_answer = retrive_from_redis(cache_lookup)
        except Exception as e:
            # Log the error but don't stop the execution
            print(f"⚠️ Redis Cache Error (Index might be missing): {e}")
            cache_answer = None
        if cache_answer is not None:
            confidence_score = cache_answer.get("confidence_score")
            metadata = cache_answer.get("meta_data")
            new_metadata = update_url(metadata)
            cache_answer["meta_data"] = new_metadata
            print("metadata:" , new_metadata)  
            print("Final output prepared.", cache_answer)
            save_chat_turn(
                session_id=session_id,
                question=query,
                answer_dict=cache_answer,
                query_vector=query_vector,
                confidence_score=confidence_score
            )
            curr_cnt = get_unique_query_count()
            if curr_cnt % K_THRESHOLD == 0:
                refresh_redis_from_sqlite(limit=5)
            return cache_answer
        
        # if query is not found in cache proceed with sqlite
        history_response = search_history_semantic(query_vector, proximity_threshold=0.95)
        if history_response:
            confidence_score = history_response["answer"].get("confidence_score")
            metadata = history_response["answer"].get("meta_data")
            new_metadata = update_url(metadata)
            history_response["answer"]["meta_data"] = new_metadata
            print(f" SQLite Semantic Hit! (Sim: {history_response['similarity']:.2f})")
            print("complete response:",history_response["answer"])
            save_chat_turn(
                session_id=session_id,
                question=query,
                answer_dict=history_response["answer"],
                query_vector=query_vector,
                confidence_score=confidence_score
            )
            curr_cnt = get_unique_query_count()
            if curr_cnt % K_THRESHOLD == 0:
                refresh_redis_from_sqlite(limit=5)
            return history_response["answer"]
        
        print(" CACHE MISS! Starting full RAG pipeline (Milvus + Rerank + Gemini)...")
        # chat_history = load_chat_conversation(session_id=session_id,last_n=2)
        # chat_history = get_recent_history(db, session_id=session_id, limit=3)
        # # print("chat_history: ",chat_history)
        # tasks = process_file(
        #     query=query,
        #     embedding_model=embedding_model,
        #     chat_history = chat_history
        # )
        
        # results=[tasks]
        # per_file_responses = [r for r in results if r]
        # # Step 2: Filter irrelevant responses
        # irrelevant_pattern = re.compile(r"(does not provide relevant information|answer is not available)", re.IGNORECASE)
        
        # # Step 3: Deduplicate metadata
        # all_meta_data = []
        # seen_files_pages = set()
        # for r in per_file_responses:
        #     all_meta_data.extend(r["metadata"])

    
        # complete_response = "\n\n".join([r["response"] for r in per_file_responses])

        # print("complete response: ",complete_response)
        # bold_words = list(set(re.findall(r"\*\*(.*?)\*\*", complete_response)))

        # # Step 5: Replace links and escape quotes
        # # html_text = replace_links(complete_response, all_meta_data)
        # # clean_output = escape_inner_quotes(html_text.strip())

        # # Convert to dict (your JSON format)
        # translated_output = json.loads(complete_response)
        # explanation_and_summary = f"{translated_output.get('Explanation')}\n\n**Summary:**\n{translated_output.get('Summary')}"
        # confidence_score = translated_output.get("Confidence_Score")
        # follow_up_question = translated_output.get("Follow_up")
        # table_data = translated_output.get("table_data")

        # # Step 6: Translation
        # if detected_lang not in ["en", "hi", "mr", "te"]:
        #     detected_lang = "en"


        # explanation_translated = output_converison(explanation_and_summary, detected_lang)
        # follow_up_translated = output_converison(follow_up_question, detected_lang)
        # table_data_translated = output_converison(table_data, detected_lang)

        # # Step 7: Final output dict
        # output = {
        #     "bold_words": bold_words,
        #     "meta_data": all_meta_data,
        #     "response":  explanation_translated ,
        #     "follow_up": follow_up_translated,
        #     "table_data": [table_data_translated],
        #     "confidence_score": confidence_score,
        #     "ucid": "99_18"  # example unique ID
        # }
        final_output = deepthink_pipeline(query,db,detected_lang,session_id=session_id)
        print("Final output prepared.", final_output)
        save_chat_turn(
            session_id=session_id,
            question=query,
            answer_dict=final_output[0],
            query_vector=query_vector,
            confidence_score=final_output[1]
            
        )

        current_cnt = get_unique_query_count()

        if current_cnt < K_THRESHOLD:
            upsert_rag_response(final_output, query, query_vector, id_gen)
        elif current_cnt % K_THRESHOLD == 0:
            refresh_redis_from_sqlite(limit=5)
        
        return final_output
    else:
        final_output = deepthink_pipeline(query,db,detected_lang,session_id=session_id)
        return final_output


        # print("going through deepthink ")
        # chat_history = get_recent_history(db, session_id=session_id, limit=3)
        # # print("chat_history: ",chat_history)
        # tasks = process_file(
        #     query=query,
        #     embedding_model=embedding_model,
        #     chat_history = chat_history
        # )
        
        # results=[tasks]
        # per_file_responses = [r for r in results if r]
        # # Step 2: Filter irrelevant responses
        # irrelevant_pattern = re.compile(r"(does not provide relevant information|answer is not available)", re.IGNORECASE)
        
        # # Step 3: Deduplicate metadata
        # all_meta_data = []
        # seen_files_pages = set()
        # for r in per_file_responses:
        #     all_meta_data.extend(r["metadata"])

    
        # complete_response = "\n\n".join([r["response"] for r in per_file_responses])

        # print("complete response: ",complete_response)
        # bold_words = list(set(re.findall(r"\*\*(.*?)\*\*", complete_response)))

        # # Step 5: Replace links and escape quotes
        # # html_text = replace_links(complete_response, all_meta_data)
        # # clean_output = escape_inner_quotes(html_text.strip())

        # # Convert to dict (your JSON format)
        # translated_output = json.loads(complete_response)
        # explanation_and_summary = f"{translated_output.get('Explanation')}\n\n**Summary:**\n{translated_output.get('Summary')}"
        # confidence_score = translated_output.get("Confidence_Score")
        # follow_up_question = translated_output.get("Follow_up")
        # table_data = translated_output.get("table_data")

        # # Step 6: Translation
        # if detected_lang not in ["en", "hi", "mr", "te"]:
        #     detected_lang = "en"


        # explanation_translated = output_converison(explanation_and_summary, detected_lang)
        # follow_up_translated = output_converison(follow_up_question, detected_lang)
        # table_data_translated = output_converison(table_data, detected_lang)

        # # Step 7: Final output dict
        # output = {
        #     "bold_words": bold_words,
        #     "meta_data": all_meta_data,
        #     "response":  explanation_translated ,
        #     "follow_up": follow_up_translated,
        #     "table_data": [table_data_translated],
        #     "confidence_score": confidence_score,
        #     "ucid": "99_18"  # example unique ID
        # }
        # print("Final output prepared.", output)
        
        
        # return output
