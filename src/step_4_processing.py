from pymilvus import connections,Collection,utility
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from vertexai.generative_models import GenerativeModel  #issue
from dotenv import load_dotenv
from src.step_5_prompt import prompt
from src.step_6_reranker import rerank_with_google

from src.llm_config import safety_settings, GENERATION_CONFIG, GENERATION_CONFIG1
from url_integration.gcs_url import generate_signed_url
from milvus_database.milvus_db import vector_search
from milvus_database.config import DB
# from src.step_7_utility import build_conversation_prompt


import os
import gc
import time
import json
import traceback


def find_url(pageno, source):
    if not source:
        return None

    source = str(source)
    if "_pages" in source:
        source = source.split("_pages")[0].strip()
    else:
            # Fallback: if "_pages" isn't there, remove the last segment if an underscore exists
        source = source.rsplit("_", 1)[0].strip() if "_" in source else source.strip()

            # Make short URL placeholder
    encoded_source = source.replace(" ", "%20")
    temp_url = f"https://storage.cloud.google.com/data-files/{encoded_source}.pdf"
    try:
        signed_url = generate_signed_url(gcs_url=temp_url)
    except Exception as exc:
        print(f"Signed URL generation failed for source={source}: {exc}")
        return None

    return f"{signed_url}#page={pageno}" if signed_url else None
    

load_dotenv()
os.environ.setdefault('GOOGLE_APPLICATION_CREDENTIALS', os.path.join(os.getcwd(), "service-account.json"))

def process_file(query, embedding_model,chat_history):
    """
    Match senior's function signature but adapted for JSON-based legal data.
    """
    query_vector = embedding_model.embed_query(query)
    print("length of query vector:", len(query_vector))
    try:
        
        print(f"\n Processing Query: {query}")

        results = vector_search(
            collection_name=DB.milvus_collection_name,
            partition_name=DB.default_partition,
            query_vectors=query_vector,
            num_results=30,
        )

        hits = results[0] if results else []
        if not hits:
            print(f" Milvus returned zero results for: {query}")

        # Step 3: Build docs
        docs,meta_data = [],[]
        for hit in hits:
            entity = hit["entity"]
            text = entity.get("text", "")
            page_no = entity.get("page_no", None)
            source = entity.get("title", None)
            # score = hit["score"]

            signed_url_with_page = find_url(page_no, source)

            doc = Document(
                page_content=str(text or ""),
                metadata={
                    "page": page_no,
                    "source": str(source or "Unknown source"),
                    "signed_url": signed_url_with_page,
                    "score": hit.get("distance")
                    
                }
            )
            docs.append(doc)
            meta_data.append(doc.metadata)
        # print("printing docs ", docs)

        # Step 4: Rerank
        start_time = time.time()
        project_id = "genai-project-463912"
        try:
            docs = rerank_with_google(query, docs, project_id)[:10]
        except Exception as rerank_error:
            print(f"Google reranker failed, using Milvus order: {rerank_error}")
            traceback.print_exc()
            docs = docs[:10]
        print("re ranking time", time.time()-start_time)

        # Step 5: Build context
        context_chunks = []
        for doc in docs:
            md = doc.metadata
            meta_line = f"[Meta: page_no={md['page']}, title={md['source']}]"
            context_chunks.append(f"{doc.page_content}-->{meta_line}\n\n")

        context = "\n\n".join(context_chunks)
        

        # Step 6: Generate LLM response
        formated_prompt = prompt.format(context=context, question=query,chat_history=chat_history)

        model = GenerativeModel("gemini-2.5-flash")
        result_new = model.generate_content(
            formated_prompt,
            generation_config=GENERATION_CONFIG,
            safety_settings=safety_settings,
        )

        # print("result_new:", result_new)

        response = result_new.candidates[0].content.parts[0].text
        # logprobs_sequence = result_new.candidates[0].logprobs_result.chosen_candidates
        print("type of response:", type(response))
        print("\n Response:", response)
        # print("\n type of Logprobs:", type(logprobs_sequence))

        final_output = {
            "query": query,
            "response": response,       
            "metadata": meta_data,
            # "confidence_score": new_response.Confidence_Score
        }
        # print("Saving new result to Semantic Cache...")
        # upsert_rag_response(
        #     rag_answer=final_output,
        #     query_text = query,
        #     query_vector=query_vector,
        #     id_generator=id_gen
        # )
        return final_output

    except Exception as e:
        print(f" Error processing query: {e}")
        traceback.print_exc()
        return None

# # --- Example Usage ---
# if __name__ == "__main__":
#     sample_query = "What does Section 1 of Bharatiya Nyaya Sanhita state?"
#     output = process_file(sample_query)
#     if output:
#         print("\n--- Response ---")
#         print(output["response"])
