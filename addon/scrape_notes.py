# scrape_notes.py
import os
import sys
import logging

# Add the path to the `libs` directory where extra packages are bundled
addon_folder = os.path.dirname(__file__)
libs_path = os.path.join(addon_folder, "libs")
if libs_path not in sys.path:
    sys.path.insert(0, libs_path)

from google.oauth2 import service_account
from googleapiclient.discovery import build

# Set up logging
logger = logging.getLogger(__name__)

# Path to the service account key file (use ENV var for flexibility)
current_dir = os.path.dirname(__file__)
SERVICE_ACCOUNT_FILE = os.path.join(current_dir, "service_account.json") 

# Define the scope
SCOPES = ['https://www.googleapis.com/auth/documents.readonly']

# Create credentials object
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# Build the Google Docs API service
service = build('docs', 'v1', credentials=credentials)

def fetch_google_doc_content(doc_id):
    """Fetches the content of a Google Doc using its ID."""
    doc = service.documents().get(documentId=doc_id).execute()
    return doc

def extract_text_from_doc(doc):
    """Extracts text from a Google Docs JSON response."""
    content = doc.get('body', {}).get('content', [])
    text = []
    
    for element in content:
        paragraph = element.get('paragraph', {})
        elements = paragraph.get('elements', [])
        for elem in elements:
            text_run = elem.get('textRun', {})
            text_content = text_run.get('content', '')
            text.append(text_content)
    
    return ''.join(text)

def scrape_notes(stage_config):
    if isinstance(stage_config, list):
        if len(stage_config) == 0:
            raise ValueError("Invalid stage_config. Expected a non-empty list or a dictionary.")
        config = stage_config[0]
    elif isinstance(stage_config, dict):
        config = stage_config
    else:
        raise ValueError("Invalid stage_config. Expected a list or a dictionary.")

    doc_id = config.get('doc_id')
    output_key = config.get('output', 'scraped_notes_output')

    if not doc_id:
        raise ValueError("Google Doc ID not provided in stage_config.")

    try:
        doc_content = fetch_google_doc_content(doc_id)
        doc_text = extract_text_from_doc(doc_content)
        return {output_key: doc_text}
    except Exception as e:
        logger.error(f"An error occurred while scraping notes: {str(e)}")
        raise
