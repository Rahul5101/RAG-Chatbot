# step_6_reranking.py
import os
from google.cloud import discoveryengine_v1 as discoveryengine

# Set service account credentials
os.environ.setdefault('GOOGLE_APPLICATION_CREDENTIALS', os.path.join(os.getcwd(), "service-account.json"))

# Project-specific configuration
PROJECT_ID = "genai-project-463912"  # replace with your project ID

def rerank_with_google(query, docs, project_id=PROJECT_ID, location="global", return_scores=False):
    """
    Re-rank retrieved documents using Google's semantic ranker.

    Args:
        query (str): User query.
        docs (List[Document]): List of Document objects to rerank.
        project_id (str): Google Cloud project ID.
        location (str): Location for Discovery Engine.
        return_scores (bool): Whether to include the ranking scores in metadata.

    Returns:
        List[Document]: Re-ranked list of Document objects.
    """
    if not docs:
        return []

    client = discoveryengine.RankServiceClient()

    # Path to the ranking configuration in Google Discovery Engine
    ranking_config = client.ranking_config_path(
        project=project_id,
        location=location,
        ranking_config="default_ranking_config",
    )

    # Prepare documents for ranking
    records = []
    for i, doc in enumerate(docs):
        page = doc.metadata.get("page")
        source = doc.metadata.get("source") or f"Doc_{i}"
        title = f"{source} page {page}" if page is not None else str(source)
        records.append(
            discoveryengine.RankingRecord(
                id=str(i),
                title=str(title),
                content=str(doc.page_content or "")
            )
        )                           

    top_n = min(len(records), len(docs))

    # Build rank request
    request = discoveryengine.RankRequest(
        ranking_config=ranking_config,
        model="semantic-ranker-default@latest",
        top_n=top_n,
        query=str(query),
        records=records,
    )

    # Call Google Discovery Engine ranker
    response = client.rank(request=request)

    # Reorder documents based on the response
    ranked_docs = []
    for r in response.records:
        idx = int(r.id)
        doc = docs[idx]
        if return_scores:
            doc.metadata["score"] = r.score
        ranked_docs.append(doc)

    return ranked_docs
