# scrape_notes.py
import os
import sys

# Add the path to the `libs` directory where extra packages are bundled
addon_folder = os.path.dirname(__file__)
libs_path = os.path.join(addon_folder, "libs")
if libs_path not in sys.path:
    sys.path.insert(0, libs_path)

from google.oauth2 import service_account
from googleapiclient.discovery import build


# Path to the service account key file (use ENV var for flexibility)
current_dir = os.path.dirname(__file__)
SERVICE_ACCOUNT_FILE = os.path.join(current_dir, "service_account.json") 
GOOGLE_DOC_ID = os.getenv('GOOGLE_DOC_ID')

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

def scrape_notes(doc_id):
    if not doc_id:
        raise ValueError("Google Doc ID not provided.")
    try:
        doc_content = fetch_google_doc_content(doc_id)
        doc_text = extract_text_from_doc(doc_content)
        return doc_text
    except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
        


