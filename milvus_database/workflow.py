from factory_client import MilvusDB
from config import DB
from milvus_db import insert_json_docs_in_milvus

from src.step_1_chunking import load_json

milvus_db = MilvusDB()
milvus_client = milvus_db.load_db()


file_path = r"C:\Users\khush\Desktop\km_ipc_be_\final_data\bns.json"
json_file= load_json(file_path=file_path)

insert_json_docs_in_milvus(json_data=json_file, partition_name=DB.default_partition , batch_size=128)