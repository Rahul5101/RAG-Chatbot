# test_insert_json_folder.py
import os
import json
print("testing")
from milvus_database.factory_client import MilvusDB
print("testing2")
from milvus_database.config import DB
print("testing3")
from milvus_database.milvus_db import insert_documents_in_milvus # your insertion function
from src.step_1_chunking import load_txt_to_docs

# -------------------------------
# Initialize Milvus
# -------------------------------
milvus_db = MilvusDB()
milvus_client = milvus_db.load_db()
milvus_db.create_partition_if_not_exists(
    collection_name=DB.milvus_collection_name,
    partition_name=DB.default_partition
)


def process_pdf_folder(root_folder: str):
    total_vectors = 0
    filewise_stats = {}

    for subdir, _, files in os.walk(root_folder):
        for file in files:
            if not file.endswith(".txt"):
                continue

            file_path = os.path.join(subdir, file)
            print(f"\n Processing JSON file: {file_path}")

            # Load + chunk JSON file
            docs = load_txt_to_docs(file_path)
            print(f"   ➝ Loaded {len(docs)} chunks from {file}")
            # Convert JSON into Milvus-docs format
            # print("+++++++++++++++++++++++++++json data",docs[0:2],"++++++++++++++++++++++++++++++++++++++++++++++++++++++")

            print(f"   ➝ Loaded {len(docs)} sections from {file}")

            # Insert into Milvus (pass converted docs, not raw JSON)
            inserted_count, skipped_count = insert_documents_in_milvus(
                docs=docs,
                partition_name=DB.default_partition,
                embed_batch_size=100,
                insert_batch_size=100
            )

            # Track stats
            filewise_stats[file_path] = {
                "inserted": inserted_count,
                "skipped": skipped_count
            }
            total_vectors += inserted_count

            print(f"   Inserted: {inserted_count}, Skipped: {skipped_count}")

    # Final summary
    print("\n --- Insertion Summary ---")
    for fpath, stats in filewise_stats.items():
        print(f"{fpath} ➝ Inserted: {stats['inserted']}, Skipped: {stats['skipped']}")
    print(f"\n Total vectors inserted across all files: {total_vectors}")


# -------------------------------
# Run on your folder
# -------------------------------
if __name__ == "__main__":
    process_pdf_folder(r"D:\valiance_sol\navy-wss\demo_data")  # replace with your PDF folder path
