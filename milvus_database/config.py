from pymilvus import connections, utility
import os
milvus_host = os.getenv("MILVUS_HOST", "localhost")
milvus_port = os.getenv("MILVUS_PORT", "19530")

class DB:
    """
    Configuration class for Milvus Database.
    Stores collection name, embedding dimensions, and other DB params.
    """

    # Default collection name (can be overridden in scripts)
    milvus_collection_name: str = "navy_wss"

    # Embedding dimensions (will be set dynamically after reading FAISS)
    model_dimensions: int = 3072

    # Local Milvus connection parameters
    # 34.180.54.232
    host: str = milvus_host
    port: str = milvus_port
    user: str = "root"
    password: str = "Milvus"

    # Default partition
    default_partition: str = "default"


# Connect to Milvus
connections.connect("default", host=DB.host, port=DB.port)

print(" Connected to Milvus!")

# Check collections
print("Available collections:", utility.list_collections())


print("Current DB: ",DB.milvus_collection_name)