from milvus_database.config import DB
import os
from milvus_database.factory_client import MilvusDB
import json
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from uuid import uuid4
from dotenv import load_dotenv
load_dotenv()
from pymilvus import Collection
from tqdm import tqdm
import time
import random
import gc


# Initialize embedding model
embedding_model = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
batch_size = 10  # adjust based on memory and Milvus performance

# Initialize Milvus client
milvus_db = MilvusDB()
milvus_client = milvus_db.load_db()

def safe_embed(model, text_or_list, retries=5):
    """
    Safely embed a single string or a list of strings with retry logic.
    """
    for attempt in range(1, retries + 1):
        try:
            # batch input → list
            # print("1")
            if isinstance(text_or_list, list):
                # print("2")
                # print("type: ",type(text_or_list))
                # print("1st item: ",text_or_list[0])
                # print("test: ",model.embed_documents(text_or_list))
                return model.embed_documents(text_or_list)

            # single input → string
            return model.embed_query(text_or_list)

        except Exception as e:
            wait = (3 ** attempt) + random.uniform(0, 1)
            print(f"[Retry {attempt+1}] Embedding failed → waiting {wait:.1f}s")
            last_exception = e
            time.sleep(wait)

    raise last_exception


def insert_documents_in_milvus(docs, partition_name="default", embed_batch_size=100,insert_batch_size=50,loop_throttle_delay=0.1):
    """
    Inserts LangChain Document objects into Milvus in batches,
    skipping duplicates using a Python set for fast lookups.
    """
    # 1. Load existing texts from Milvus once
    existing_texts = get_existing_texts(partition_name)
    print(f"🔍 Found {len(existing_texts)} existing records in Milvus")

    total = len(docs)
    embed_batch =[]
    metadata_batch=[]
    buffer = []
    total_docs = 0
    skipped = 0

    with tqdm(total=total,desc=f"Inserting into {partition_name}") as pbar:

        for doc in docs:
            text = doc.page_content.strip()
            title = doc.metadata.get("title", "")
            # url = doc.metadata.get("url", None)
            page_no_str = doc.metadata.get("page_no", None)
            page_no = int(page_no_str) if page_no_str is not None else None

            # Skip if text already exists
            if text in existing_texts:
                skipped += 1
                pbar.update(1)
                continue  
            
            # Generate embedding
            embed_batch.append(text)
            metadata_batch.append((title,page_no))
            existing_texts.add(text)

            if len(embed_batch) >= embed_batch_size:
                print("just loading before embeddings ")
                embeddings = safe_embed(embedding_model, embed_batch)
                print("just loading after embeddings ")


                for text, (title,page_no),embedding in zip(embed_batch,metadata_batch,embeddings):
                    payload = {
                        "uuid_id": str(uuid4()),
                        "text": text,
                        "title": title,
                        "page_no":page_no,
                        "vector": embedding
                    }
                    buffer.append(payload)
                    total_docs += 1
                
                embed_batch.clear()
                metadata_batch.clear()

                if len(buffer) >= insert_batch_size:
                    batch_count = len(buffer)
                    insert_partition_data_in_collection(partition_name, buffer)
                    print(f"✅ Inserted {batch_count} new docs (Total so far: {total_docs})")
                    buffer.clear()
                    gc.collect()

                    time.sleep(loop_throttle_delay)
            pbar.update(1)


       

        # Insert any remaining records
        if embed_batch:
            embeddings = safe_embed(embedding_model,embed_batch)
            for text, (title,page_no), embedding in zip(embed_batch,metadata_batch,embeddings):
                payload = {
                    "uuid_id": str(uuid4()),
                    "text": text,
                    "title": title,
                    "page_no":page_no,
                    "vector": embedding
                }
                buffer.append(payload)               
                total_docs += 1
            embed_batch.clear()
            metadata_batch.clear()              

        if buffer:
            batch_count = len(buffer)
            insert_partition_data_in_collection(partition_name, buffer)
            print(f"✅ Inserted final {batch_count} docs (Total: {total_docs})")
            buffer.clear()
            gc.collect()




    print(f"🎯 Finished: Inserted {total_docs} new docs, Skipped {skipped} duplicates.")

    return total_docs, skipped


def get_existing_texts(partition_name):
    """
    Fetches all existing texts from a Milvus partition and returns a Python set.
    """
    from pymilvus import Collection
    collection = Collection(DB.milvus_collection_name)
    collection.load()

    existing_texts = set()
    offset = 0
    limit = 2000  # fetch in chunks to avoid memory issues

    while True:
        res = collection.query(
            expr="",  # no filter
            output_fields=["text"],  # must match Milvus collection field!
            partition_names=[partition_name],
            offset=offset,
            limit=limit
        )
        if not res:
            break
        for r in res:
            existing_texts.add(r["text"])  # 'text' matches Milvus field name
        offset += limit

    return existing_texts



def insert_partition_data_in_collection(partition_name, data):
    """Insert batch data into Milvus partition"""
    collection_name = DB.milvus_collection_name
    if not milvus_client.has_collection(collection_name):
        milvus_client.create_milvus_collection_if_not_exists(collection_name)
    return milvus_db.insert_data(partition_name=partition_name, data=data)


def vector_search(collection_name, partition_name, query_vectors, num_results):
    res = milvus_client.search(
        collection_name=collection_name,
        partition_names=[partition_name],
        data=[query_vectors],
        limit=num_results,
        search_params={"metric_type": "COSINE", "params": {"nprobe": 10}},
        output_fields=["text", "title", "page_no"]
    )
    return res


def retrieve_all_collections():
    return milvus_client.list_collections()


def unique_results(res):
    seen_texts = set()
    unique_results = []
    for result in res[0]:
        text = result['entity']['text']
        if text not in seen_texts:
            seen_texts.add(text)
            unique_results.append(result)
    return unique_results


def retrieve_collection_schema(collection_name):
    try:
        schema = milvus_client.describe_collection(collection_name)
        print(f"Collection: {schema}")
    except Exception as e:
        print(f"Error retrieving schema for collection '{collection_name}': {e}")


def retrieve_all_data_in_schema(collection_name):
    return milvus_client.get_collection_stats(collection_name=collection_name)


def vector_search_truths(partition_names, query_embeddings):
    try:
        collection_name = DB.milvus_collection_name
        existing_partitions = [
            p for p in partition_names if milvus_db.model.has_partition(
                collection_name=collection_name,
                partition_name=p
            )
        ]
        if not existing_partitions:
            return []

        results = milvus_db.model.search(
            collection_name=collection_name,
            data=query_embeddings,
            limit=40,
            output_fields=["text"],
            partition_names=existing_partitions,
            search_params={"metric_type": "COSINE", "params": {"nprobe": 10}}
        )
        return results

    except Exception as e:
        print(f"Error retrieving partition data: {e}")
        return []


def delete_partition(collection_name, partition_name):
    milvus_db.drop_partition(collection_name=collection_name, partition_name=partition_name)
    print(f"Deleted partition {partition_name} from collection {collection_name}")
