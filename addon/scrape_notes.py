# scrape_notes.py
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Path to the service account key file (use ENV var for flexibility)
SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE', '/app/service_account.json')
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
        doc_content = fetch_google_doc_content(GOOGLE_DOC_ID)
        doc_text = extract_text_from_doc(doc_content)
        return doc_text
    except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
        


