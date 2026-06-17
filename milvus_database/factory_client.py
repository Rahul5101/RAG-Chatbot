from pymilvus import (
    connections,
    utility,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
    MilvusClient
)
from milvus_database.config import DB
import os
milvus_host = os.getenv("MILVUS_HOST", "localhost")
milvus_port = os.getenv("MILVUS_PORT", "19530")
class MilvusDB:
    def __init__(self, client_path=None):
        self.client_path = client_path
        connections.connect(
            alias="default",
            host=milvus_host,  # to connect to VM '34.100.163.108' / to run in VM 'milvus-standalone' / to run in local with docker 'localhost'
            port=milvus_port,  # Milvus port exposed by your container
            user='root',  # If authentication is enabled
            password='Milvus'  # If authentication is enabled
        )
        self.model = MilvusClient(
            uri=f"tcp://{milvus_host}:{milvus_port}",  # to connect to VM '34.100.163.108:19530' / to run in VM 'milvus-standalone' / to run in local with docker 'localhost'
            token="root:Milvus"  # username:password format
        )

    def load_db(self):
        self.create_milvus_collection_if_not_exists()
        print("Milvus loaded in memory")
        return self.model

    def create_milvus_collection_if_not_exists(self):
        try:
            has_collection = self.model.has_collection(DB.milvus_collection_name, timeout=5)
            if has_collection:
                print(f"{DB.milvus_collection_name} collection Exists")
                return True
            print(f"Creating Collection: {DB.milvus_collection_name}")
            schema = self.model.create_schema(enable_dynamic_field=True)
            schema.add_field(field_name="uuid_id", datatype=DataType.VARCHAR, max_length=65, is_primary=True)
            schema.add_field(field_name="text", datatype=DataType.VARCHAR, max_length=5000)
            schema.add_field(field_name="title", datatype=DataType.VARCHAR,max_length=512)
            schema.add_field(field_name="page_no",datatype=DataType.INT64,nullable=True) #adding new column page no 
            schema.add_field(field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=3072)
            index_params = self.model.prepare_index_params()

            print("testing")

            index_params.add_index(
                field_name="vector",
                metric_type="COSINE",
                index_type="HNSW",
                index_name="vector_hnsw",
                params={"M": 16, "efConstruction": 200}
            )

            self.model.create_collection(DB.milvus_collection_name, schema=schema, index_params=index_params,
                                         consistency_level="Strong")
            
        except Exception as e:
            print(f"Error checking milvus db path at {self.client_path}: {e}")
            return False

    def drop_collection(self):
        """Drops a specified collection if it exists."""
        try:
            if utility.has_collection(DB.milvus_collection_name):
                utility.drop_collection(DB.milvus_collection_name)
                print(f"✅ Dropped collection: {DB.milvus_collection_name}")
            else:
                print(f"⚠️ Collection {DB.milvus_collection_name} does not exist.")
        except Exception as e:
            print(f"Error dropping collection '{DB.milvus_collection_name}': {e}")

    def create_partition_if_not_exists(self, collection_name, partition_name):
        """Creates a partition for a table if it doesn't exist"""
        try:
            if not self.model.has_partition(collection_name, partition_name):
                print(f'Creating partition {partition_name}')
                self.model.create_partition(
                    collection_name=collection_name,
                    partition_name=partition_name,
                )
                print(f"Created partition {partition_name} in collection {collection_name}")
        except Exception as e:
            print(f"Error creating partition for table {partition_name}: {e}")

    def insert_data(self, partition_name, data):
        try:
            collection_name = DB.milvus_collection_name

            self.create_partition_if_not_exists(collection_name, partition_name)

            return self.model.insert(
                collection_name=collection_name,
                data=data,
                partition_name=partition_name
            )
        except Exception as e:
            print(f"Error inserting data: {e}")
            return None

    def release_partitions(self, collection_name, partition_names):
        """Releases partitions from memory"""
        try:
            self.model.release_partitions(
                collection_name=collection_name,
                partition_names=partition_names
            )
        except Exception as e:
            print(f"Error releasing partitions: {e}")

    def drop_partition(self, collection_name, partition_name):
        """Drops a partition from a collection"""
        try:
            # First release the partition
            self.release_partitions(collection_name, [partition_name])

            # Then drop it
            self.model.drop_partition(
                collection_name=collection_name,
                partition_name=partition_name
            )
        except Exception as e:
            print(f"Error dropping partition: {e}")



