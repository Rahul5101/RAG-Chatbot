from milvus_database.factory_client import MilvusDB
from milvus_database.config import DB


MilvusDB.drop_collection(DB.milvus_collection_name)
