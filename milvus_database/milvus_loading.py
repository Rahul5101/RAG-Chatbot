from milvus_database.factory_client import MilvusDB
from milvus_database.config import DB
from pymilvus import connections, Collection
import os
milvus_host = os.getenv("MILVUS_HOST", "localhost")
milvus_port = os.getenv("MILVUS_PORT", "19530")
def loading_milvus():
    try:
        # Try to connect to Milvus
        connections.connect("default", host=milvus_host, port=milvus_port)
        print(":white_check_mark: Connected to Milvus!")
        collection = Collection(name=DB.milvus_collection_name)
        collection.load()
        print("Collection loaded")
    except Exception as e:
        # If connection fails, initialize and set up
        print(":warning: Milvus connection failed, initializing database...")
        milvus_db = MilvusDB()
        milvus_client = milvus_db.load_db()
        milvus_db.create_partition_if_not_exists(
            collection_name=DB.milvus_collection_name,
            partition_name=DB.default_partition
        )