import os
import re
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

def load_txt_to_docs(file_path: str):
    """
    Reads content from a plain text (.txt) file where pages are in the format:
    Page X: <content>

    Converts each page into a LangChain Document with metadata:
    - page_no
    - title (file name without extension)
    """

    docs = []

    try:
        with open(file_path, "r", encoding="latin-1") as f:
            content = f.read()
    except Exception as e:
        print(f" Error reading file {file_path}: {e}")
        return []

    if not content.strip():
        print(f"⚠️ Warning: Text file {file_path} is empty.")
        return []

    file_name = os.path.basename(file_path)
    title = os.path.splitext(file_name)[0]

    # 🔹 Regex to capture Page number and content
    pattern = re.compile(
        r'Page\s+(\d+)\s*:\s*(.*?)(?=\nPage\s+\d+\s*:|$)',
        re.DOTALL
    )

    matches = pattern.findall(content)

    if not matches:
        print(f"⚠️ No page markers found in {file_path}")
        return []

    for page_no, page_content in matches:
        page_content = page_content.strip()

        if not page_content:
            continue

        docs.append(
            Document(
                page_content=page_content,
                metadata={
                    "page_no": int(page_no),
                    "title": title
                }
            )
        )

    # 🔹 Chunk the documents
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=150
    )

    split_docs = splitter.split_documents(docs)

    return split_docs


# # Example usage
# if __name__ == "__main__":
#     chunks = load_json(r"final_data/bns.json")
#     print(f"Total chunks created: {len(chunks)}")
#     print("\npage content::",chunks[0].page_content)
#     print("\nmetadata::",chunks[0].metadata)
