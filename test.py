from milvus_database.config import DB
from milvus_database.factory_client import MilvusDB
from src.step_3_llm_loaders import main
import os
from dotenv import load_dotenv
load_dotenv()
import asyncio
import time
from milvus_database.milvus_loading import loading_milvus
print("testing")
start = time.time()
# loading_milvus()
session_id = "test_session02"
# query = "hi my name is rahul gupta and tell me about the piping arrangements in the cargo oil?"
# query = "what is my name?"
# query = "how to examine the athwartship thrust propellers?"
# query = "tell me about the Single and double hull chemical tankers?"
query = "Given the evolution of Arctic routes, how adequate are the 2016 LR ice and winterisation rules in addressing future operational and structural challenges?"


print("query: ",query)
response = asyncio.run(main(query=query,detected_lang="en",session_id=session_id,answer_type="think"))
elapsed_time = time.time() - start
print("Total time", elapsed_time)

