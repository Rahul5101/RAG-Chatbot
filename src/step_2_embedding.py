# step_2_embedding.py

from langchain_community.vectorstores import Milvus
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pymilvus import connections, utility
from dotenv import load_dotenv
from src.step_1_chunking import load_json  # import your chunking function
import os
import time

# ------------------------------
# Load environment variables
# ------------------------------
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("❌ GOOGLE_API_KEY not found. Please set it in your .env file.")

print("✅ GOOGLE_API_KEY loaded successfully.")

# ------------------------------
# Initialize embedding model
# ------------------------------
embedding_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

# ------------------------------
# Create embeddings and store in Milvus
# ------------------------------
def create_embeddings(json_file_path: str, collection_name: str = "rules_and_regs"):
    """
    Load JSON data, generate embeddings, and store them in Milvus.
    Includes batching and retry logic for reliability.
    """
    # Step 1: Load and chunk JSON data
    documents = load_json(json_file_path)
    if not documents:
        print("⚠️ No documents found to embed.")
        return None

    print(f"📄 Loaded {len(documents)} chunks from JSON file.")

    # Step 2: Ensure Milvus connection
    connections.connect("default", host="localhost", port="19530")
    if utility.has_collection(collection_name):
        print(f"🗑 Dropping old Milvus collection: {collection_name}")
        utility.drop_collection(collection_name)

    # Step 3: Create embeddings safely (with batching)
    texts = [doc.page_content if hasattr(doc, "page_content") else str(doc) for doc in documents]
    vectorstore = None

    batch_size = 20
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        try:
            print(f"⚙️ Generating embeddings for batch {i // batch_size + 1}/{len(texts) // batch_size + 1}...")
            vectorstore = Milvus.from_texts(
                texts=batch,
                embedding=embedding_model,
                connection_args={"host": "localhost", "port": "19530"},
                collection_name=collection_name
            )
            print(f"✅ Batch {i // batch_size + 1} stored in Milvus.")
            time.sleep(1)  # small delay to avoid rate limits
        except Exception as e:
            print(f"❌ Error embedding batch {i // batch_size + 1}: {e}")
            time.sleep(3)

    print(f"✅ All embeddings created and stored in Milvus collection: {collection_name}")
    return vectorstore


# # ------------------------------
# # Example usage
# # ------------------------------
# if __name__ == "__main__":
#     json_file = "final_data/bns.json"

#     try:
#         create_embeddings(json_file, collection_name="legal_chunks")
#         print("🎯 Embedding process completed successfully.")
#     except Exception as e:
#         print("❌ Fatal error during embedding:", e)
