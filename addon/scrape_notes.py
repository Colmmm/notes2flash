import os
import sys
import logging
import json
import difflib
import requests
from datetime import datetime

# Add the path to the `libs` directory where extra packages are bundled
addon_folder = os.path.dirname(__file__)
libs_path = os.path.join(addon_folder, "libs")
if libs_path not in sys.path:
    sys.path.insert(0, libs_path)

# Set up logging
logger = logging.getLogger(__name__)

# Path to the service account key file
current_dir = os.path.dirname(__file__)
SERVICE_ACCOUNT_FILE = os.path.join(current_dir, "service_account.json")
TRACKED_DOCS_FILE = os.path.join(current_dir, "tracked_docs.json")

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
        
        # Return a document-like structure to maintain compatibility
        content = response.text
        return {
            'body': {
                'content': [{'paragraph': {'elements': [{'textRun': {'content': line}}]}} 
                          for line in content.split('\n')]
            },
            'revisionId': None  # Public docs don't provide revision info
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch public document: {str(e)}")
        raise ValueError(f"Failed to fetch public document. Ensure the document is publicly accessible: {str(e)}")

def load_tracked_documents():
    """Load tracked documents from JSON file."""
    if os.path.exists(TRACKED_DOCS_FILE):
        with open(TRACKED_DOCS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_tracked_documents(tracked_docs):
    """Save tracked documents to JSON file."""
    with open(TRACKED_DOCS_FILE, 'w') as f:
        json.dump(tracked_docs, f, indent=4)
    logger.info(f"Tracked documents saved to {TRACKED_DOCS_FILE}")

def get_document_state(doc_id):
    """Get previously stored state for a document."""
    tracked_docs = load_tracked_documents()
    return tracked_docs.get(doc_id, {
        'lines': [],
        'last_updated': None,
        'version': None,
        'successfully_added_to_anki': False,
        'pending_changes': []
    })

def update_document_state(doc_id, lines, version=None, successfully_added_to_anki=False, pending_changes=None):
    """Update the stored state for a document."""
    tracked_docs = load_tracked_documents()
    tracked_docs[doc_id] = {
        'lines': lines,
        'last_updated': datetime.now().isoformat(),
        'version': version,
        'successfully_added_to_anki': successfully_added_to_anki,
        'pending_changes': pending_changes if pending_changes is not None else []
    }
    save_tracked_documents(tracked_docs)

def mark_document_as_processed(doc_id):
    """Mark a document as successfully processed."""
    tracked_docs = load_tracked_documents()
    if doc_id in tracked_docs:
        tracked_docs[doc_id]['successfully_added_to_anki'] = True
        tracked_docs[doc_id]['pending_changes'] = []
        save_tracked_documents(tracked_docs)
        logger.info(f"Document {doc_id} marked as successfully processed")

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

def extract_text_from_doc(doc):
    """Extracts text from a Google Docs JSON response with improved formatting handling."""
    content = doc.get('body', {}).get('content', [])
    text_lines = []
    current_line = []
    
    def process_element(element):
        if 'paragraph' in element:
            paragraph = element['paragraph']
            
            # Handle paragraph style
            style = paragraph.get('paragraphStyle', {})
            if style.get('namedStyleType') in ['HEADING_1', 'HEADING_2', 'HEADING_3']:
                current_line.append('\n')  # Add extra line break for headings
            
            # Process text elements
            for elem in paragraph.get('elements', []):
                if 'textRun' in elem:
                    text = elem['textRun'].get('content', '')
                    if text.strip():  # Only add non-empty text
                        current_line.append(text)
            
            # Handle end of paragraph
            line_text = ''.join(current_line).strip()
            if line_text:
                text_lines.append(line_text)
            current_line.clear()
            
        elif 'table' in element:
            # Handle tables (simplified)
            text_lines.append('\n[Table Content]\n')
        
        elif 'sectionBreak' in element:
            text_lines.append('\n')
    
    for element in content:
        process_element(element)
    
    return [line for line in text_lines if line.strip()]

def compare_document_versions(old_lines, new_lines):
    """Compare two versions of document content and return changes."""
    # Create sets for efficient comparison
    old_set = set(old_lines)
    new_set = set(new_lines)
    
    # Find added lines (including those at the beginning)
    added_lines = list(new_set - old_set)
    
    # Find modified lines using difflib for more accurate comparison
    differ = difflib.Differ()
    diff = list(differ.compare(old_lines, new_lines))
    
    modified_lines = []
    for i, line in enumerate(diff):
        if line.startswith('- '):
            old_text = line[2:]
            # Look ahead for potential modifications
            for j in range(i + 1, min(i + 3, len(diff))):
                if diff[j].startswith('+ '):
                    new_text = diff[j][2:]
                    # Check if the lines are similar but not identical
                    similarity = difflib.SequenceMatcher(None, old_text, new_text).ratio()
                    if 0.5 < similarity < 1.0:
                        modified_lines.append(new_text)
                        break
    
    # Remove any modified lines from added lines to avoid duplicates
    added_lines = [line for line in added_lines if line not in modified_lines]
    
    return {
        'added': added_lines,
        'modified': modified_lines,
        'total_changes': len(added_lines) + len(modified_lines)
    }

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
        
        # Fetch current document state
        doc_content = fetch_google_doc_content(doc_id)
        current_version = doc_content.get('revisionId')
        current_lines = extract_text_from_doc(doc_content)

        # Get previous state
        prev_state = get_document_state(doc_id)
        prev_lines = prev_state['lines']
        prev_version = prev_state['version']
        prev_processed = prev_state.get('successfully_added_to_anki', False)
        pending_changes = prev_state.get('pending_changes', [])

        # For new documents or first-time processing
        if not prev_lines:
            logger.info(f"New document detected. Initializing tracking for document ID: {doc_id}")
            content_str = '\n\n'.join(current_lines)
            update_document_state(doc_id, current_lines, current_version, False, current_lines)
            return {output_key: content_str}

        # Compare versions and get changes
        changes = compare_document_versions(prev_lines, current_lines)
        
        # If there are new changes, process them
        if changes['total_changes'] > 0:
            logger.info(f"Found {changes['total_changes']} changes in document {doc_id}")
            lines_to_process = changes['added'] + changes['modified']
            content_str = '\n\n'.join(lines_to_process)
            update_document_state(doc_id, current_lines, current_version, False, lines_to_process)
            return {output_key: content_str}
        
        # If there are pending changes from a previous failed attempt, process only those
        if pending_changes:
            logger.info(f"Processing {len(pending_changes)} pending changes from previous attempt")
            content_str = '\n\n'.join(pending_changes)
            # Don't update the document state here as we're still working with the same pending changes
            return {output_key: content_str}

        # No changes and no pending changes
        logger.info(f"No changes detected in document {doc_id}")
        raise ValueError("No changes detected in document. Skipping further processing.")

    except Exception as e:
        logger.error(f"An error occurred while scraping notes: {str(e)}")
        raise
