import os
import logging
import requests
from .scrape_utils import (
    SERVICE_ACCOUNT_FILE,
    extract_text_from_doc,
    logger
)

def is_service_account_available():
    """Check if service account credentials are available."""
    return os.path.exists(SERVICE_ACCOUNT_FILE)

def initialize_api_client():
    """Initialize the Google Docs API client if service account is available."""
    if not is_service_account_available():
        return None
    
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        SCOPES = ['https://www.googleapis.com/auth/documents.readonly']
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        return build('docs', 'v1', credentials=credentials)
    except Exception as e:
        logger.error(f"Failed to initialize API client: {str(e)}")
        return None

def fetch_public_doc_content(doc_id):
    """Fetches content from a public Google Doc using HTTP requests."""
    try:
        url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
        response = requests.get(url)
        response.raise_for_status()
        
        content = response.text
        return {
            'body': {
                'content': [{'paragraph': {'elements': [{'textRun': {'content': line}}]}} 
                          for line in content.split('\n')]
            },
            'revisionId': None
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch public document: {str(e)}")
        raise ValueError(f"Failed to fetch public document. Ensure the document is publicly accessible: {str(e)}")

def fetch_google_doc_content(doc_id):
    """Fetches the content of a Google Doc using either API or public access."""
    service = initialize_api_client()
    
    if service:
        logger.info("Using authenticated access via service account")
        try:
            return service.documents().get(documentId=doc_id).execute()
        except Exception as e:
            logger.error(f"API access failed: {str(e)}")
            raise ValueError(f"Failed to fetch document via API: {str(e)}")
    else:
        logger.info("Using public access method (service account not available)")
        return fetch_public_doc_content(doc_id)
