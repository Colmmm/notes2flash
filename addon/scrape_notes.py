import logging
from .scrape_utils import (
    parse_url,
    get_document_state,
    update_document_state,
    compare_document_versions,
    extract_text_from_doc,
    mark_document_as_processed,  # Re-export this
    logger
)
from .scrape_googledoc import fetch_google_doc_content
from .scrape_notion import scrape_notion_page
from .scrape_obsidian import scrape_obsius_note

# Re-export utility functions that other modules depend on
__all__ = ['scrape_notes', 'mark_document_as_processed', 'get_document_state', 'update_document_state']

def scrape_notes(stage_config):
    if isinstance(stage_config, list):
        if len(stage_config) == 0:
            raise ValueError("Invalid stage_config. Expected a non-empty list or a dictionary.")
        config = stage_config[0]
    elif isinstance(stage_config, dict):
        config = stage_config
    else:
        raise ValueError("Invalid stage_config. Expected a list or a dictionary.")

    url = config.get('url')
    output_key = config.get('output', 'scraped_notes_output')

    if not url:
        raise ValueError("URL not provided in stage_config.")

    try:
        # Parse URL to determine source type
        source_info = parse_url(url)
        source_type = source_info['type']
        source_id = source_info['id']
        
        # Fetch content based on source type
        doc_content = None
        if source_type == 'google_docs':
            doc_content = fetch_google_doc_content(source_id)
        elif source_type == 'notion':
            doc_content = scrape_notion_page(url)
        elif source_type == 'obsius':
            doc_content = scrape_obsius_note(url)
        else:
            raise ValueError(f"Unsupported source type: {source_type}")
            
        if doc_content is None:
            logger.error(f"Failed to fetch content from {source_type} source: {url}")
            raise ValueError(f"Failed to fetch content from {source_type} source: {url}")

        # For Google Docs, we have revision info
        current_version = None
        if source_type == 'google_docs':
            current_version = doc_content.get('revisionId')
        elif isinstance(doc_content, dict) and 'version' in doc_content:
            current_version = doc_content.get('version')

        # Extract text content
        if source_type == 'obsius':
            # For Obsius, the content is already in the correct format
            current_lines = doc_content.get('content', '').split('\n')
            if not current_lines:
                raise ValueError(f"No content found in Obsius note: {url}")
        else:
            current_lines = extract_text_from_doc(doc_content)

        # Get previous state
        prev_state = get_document_state(source_id)
        prev_lines = prev_state['lines']
        prev_version = prev_state['version']
        prev_processed = prev_state.get('successfully_added_to_anki', False)
        pending_changes = prev_state.get('pending_changes', [])

        # For new documents or first-time processing
        if not prev_lines:
            logger.info(f"New document detected. Initializing tracking for document ID: {source_id}")
            content_str = '\n\n'.join(current_lines)
            update_document_state(source_id, current_lines, current_version, False, current_lines)
            return {output_key: content_str}

        # Compare versions and get changes
        changes = compare_document_versions(prev_lines, current_lines)
        
        # If there are new changes, process them
        if changes['total_changes'] > 0:
            logger.info(f"Found {changes['total_changes']} changes in document {source_id}")
            lines_to_process = changes['added'] + changes['modified']
            content_str = '\n\n'.join(lines_to_process)
            update_document_state(source_id, current_lines, current_version, False, lines_to_process)
            return {output_key: content_str}
        
        # If there are pending changes from a previous failed attempt, process only those
        if pending_changes:
            logger.info(f"Processing {len(pending_changes)} pending changes from previous attempt")
            content_str = '\n\n'.join(pending_changes)
            return {output_key: content_str}

        # No changes and no pending changes
        logger.info(f"No changes detected in document {source_id}")
        raise ValueError("No changes detected in document. Skipping further processing.")

    except Exception as e:
        logger.error(f"An error occurred while scraping notes: {str(e)}")
        raise
