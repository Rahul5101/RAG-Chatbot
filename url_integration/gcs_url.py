from urllib.parse import urlparse, unquote
from google.cloud import storage
from datetime import timedelta
from google.oauth2 import service_account
import os

def generate_signed_url(gcs_url: str, expires_in_minutes: int = 120) -> str:
    """
    Always generate a fresh signed URL for GCS objects.
    Supports:
      - Already signed URLs (extracts blob path and re-signs)
      - Full GCS console-style URLs
      - Raw blob paths (videos/... or processed/...)
    """

    # Load service account credentials explicitly
    service_account_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "service-account.json")
    credentials = service_account.Credentials.from_service_account_file(service_account_path)


    if not gcs_url:
        return None
    client = storage.Client(credentials=credentials)
    bucket_name = " data-files"
    # Case 1: Signed or console-style URL → extract blob path
    if gcs_url.startswith("http"):
        parsed = urlparse(gcs_url)
        path_parts = parsed.path.lstrip("/").split("/", 1)
        if len(path_parts) < 2:
            return gcs_url
        bucket_name = path_parts[0]
        blob_name = unquote(path_parts[1].split("?")[0])
    else:
        blob_name = gcs_url
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    return blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=expires_in_minutes),
        method="GET"
    )


