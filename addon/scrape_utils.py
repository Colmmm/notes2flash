import os
import sys
import logging
import json
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import difflib

# Add the path to the `libs` directory where extra packages are bundled
addon_folder = os.path.dirname(__file__)
libs_path = os.path.join(addon_folder, "libs")
if libs_path not in sys.path:
    sys.path.insert(0, libs_path)

# Set up logging
logger = logging.getLogger("notes2flash")

# Path to config and tracked docs files
current_dir = os.path.dirname(__file__)
SERVICE_ACCOUNT_FILE = os.path.join(current_dir, "service_account.json")
TRACKED_DOCS_FILE = os.path.join(current_dir, "tracked_docs.json")
CONFIG_FILE = os.path.join(current_dir, "config.json")

def load_config():
    """Load configuration from config.json."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {str(e)}")
        return {}

def format_notion_id(page_id):
    """Format a Notion page ID into UUID format."""
    # Remove any hyphens that might already exist
    clean_id = page_id.replace('-', '')
    
    # Ensure we have exactly 32 characters
    if len(clean_id) != 32:
        raise ValueError(f"Invalid Notion page ID length: {len(clean_id)}")
    
    # Format into UUID (8-4-4-4-12)
    return f"{clean_id[:8]}-{clean_id[8:12]}-{clean_id[12:16]}-{clean_id[16:20]}-{clean_id[20:]}"

def looks_like_notion_id(text):
    """Check if a string looks like a Notion page ID."""
    # Remove any hyphens that might exist
    clean_text = text.replace('-', '')
    # Check if it's a 32-character hexadecimal string
    return len(clean_text) == 32 and all(c in '0123456789abcdefABCDEF' for c in clean_text)

def parse_url(url):
    """Parse URL to determine source type and extract relevant ID."""
    parsed = urlparse(url)
    
    # Handle Google Docs URLs
    if 'docs.google.com' in parsed.netloc:
        # Extract doc ID from URL
        if '/d/' in parsed.path:
            doc_id = parsed.path.split('/d/')[1].split('/')[0]
        else:
            doc_id = parse_qs(parsed.query).get('id', [None])[0]
        
        if doc_id:
            return {'type': 'google_docs', 'id': doc_id}
    
    # Handle Notion URLs
    elif 'notion.site' in parsed.netloc or 'notion.so' in parsed.netloc:
        # Extract page ID (last part of the URL)
        page_id = parsed.path.split('-')[-1]  # Get the last part after the last hyphen
        if page_id:
            try:
                # Format the ID into UUID format
                uuid_id = format_notion_id(page_id)
                return {'type': 'notion', 'id': uuid_id}
            except ValueError as e:
                raise ValueError(f"Invalid Notion page ID: {str(e)}")
    
    # Handle Obsius URLs
    elif 'obsius.site' in parsed.netloc:
        # Extract note ID from path
        note_id = parsed.path.lstrip('/')
        if note_id:
            return {'type': 'obsius', 'id': note_id}
    
    # Handle direct IDs (Google Docs, Notion, and Obsius)
    elif not parsed.scheme and not parsed.netloc:
        # If it looks like a Notion ID (32 chars, hex)
        if looks_like_notion_id(url):
            try:
                uuid_id = format_notion_id(url)
                return {'type': 'notion', 'id': uuid_id}
            except ValueError as e:
                raise ValueError(f"Invalid Notion page ID: {str(e)}")
        # If it looks like a Google Doc ID (long alphanumeric string)
        elif len(url) > 25 and url.isalnum():
            return {'type': 'google_docs', 'id': url}
        # If it looks like an Obsius ID (shorter alphanumeric string)
        elif url.isalnum():
            return {'type': 'obsius', 'id': url}
    
    raise ValueError(f"Unsupported URL format: {url}")

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
        'pending_changes': [],
        'source_url': None,
        'source_type': None
    })

def update_document_state(doc_id, lines, version=None, successfully_added_to_anki=False, pending_changes=None, source_url=None, source_type=None):
    """Update the stored state for a document."""
    tracked_docs = load_tracked_documents()
    current_state = tracked_docs.get(doc_id, {})
    
    tracked_docs[doc_id] = {
        'lines': lines,
        'last_updated': datetime.now().isoformat(),
        'version': version,
        'successfully_added_to_anki': successfully_added_to_anki,
        'pending_changes': pending_changes if pending_changes is not None else [],
        'source_url': source_url if source_url is not None else current_state.get('source_url'),
        'source_type': source_type if source_type is not None else current_state.get('source_type')
    }
    save_tracked_documents(tracked_docs)
    logger.info(f"Updated state for document {doc_id}")

def mark_document_as_processed(doc_id):
    """Mark a document as successfully processed."""
    tracked_docs = load_tracked_documents()
    if doc_id in tracked_docs:
        # Preserve source_url and source_type while updating status
        tracked_docs[doc_id].update({
            'successfully_added_to_anki': True,
            'pending_changes': []
        })
        save_tracked_documents(tracked_docs)
        logger.info(f"Document {doc_id} marked as successfully processed")
    else:
        logger.warning(f"Attempted to mark non-existent document {doc_id} as processed")

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
