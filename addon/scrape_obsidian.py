import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict
import logging
from .scrape_utils import (
    parse_url, 
    get_document_state,
    update_document_state,
    mark_document_as_processed
)

# Set up logging
logger = logging.getLogger(__name__)

def extract_obsius_id(url: str) -> Optional[str]:
    """
    Extracts the unique ID from an Obsius URL.
    
    Args:
        url (str): The URL of the Obsius note
        
    Returns:
        Optional[str]: The unique ID if valid URL, None otherwise
    """
    try:
        # Split URL and get the last part (the ID)
        parts = url.rstrip(')').split('/')
        if len(parts) > 0:
            return parts[-1]
        return None
    except Exception as e:
        logger.error(f"Failed to extract Obsius ID from URL {url}: {str(e)}")
        return None

def scrape_obsius_note(url: str) -> Optional[Dict]:
    """
    Scrapes content from an Obsius-published Obsidian note.
    
    Args:
        url (str): The URL of the Obsius note (format: https://obsius.site/{unique_id})
        
    Returns:
        Optional[Dict]: Dictionary containing content and metadata if successful, None if failed
    """
    try:
        # Extract Obsius ID
        obsius_id = extract_obsius_id(url)
        if not obsius_id:
            logger.error(f"Invalid Obsius URL format: {url}")
            return None
            
        # Check document state
        doc_state = get_document_state(obsius_id)
        
        # Send GET request to the URL
        logger.info(f"Fetching Obsius note: {url}")
        response = requests.get(url, timeout=10)  # Add timeout
        
        # Check for 404 first
        if response.status_code == 404:
            logger.error(f"Note not found at URL (404): {url}")
            return None
            
        # Check other status codes
        response.raise_for_status()
        
        # Parse HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check for 404 page content
        if soup.find('h1', string='404') or soup.find('h2', string='Post not found'):
            logger.error(f"Note not found at URL (content indicates 404): {url}")
            return None
            
        # Extract text content, preserving basic formatting
        content = []
        main_content = soup.find('body')
        
        if not main_content:
            logger.error(f"No content found in Obsius note: {url}")
            return None
            
        for element in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li']):
            if element.name.startswith('h'):
                # Preserve headers with appropriate markdown syntax
                level = int(element.name[1])
                header_text = element.get_text().strip()
                if header_text and header_text not in ['404', 'Post not found']:
                    content.append('#' * level + ' ' + header_text)
            elif element.name == 'li':
                # Preserve list items
                content.append('- ' + element.get_text().strip())
            else:
                text = element.get_text().strip()
                if text and text not in ['404', 'Post not found']:
                    content.append(text)
        
        # Filter out empty lines and join with newlines
        processed_content = '\n'.join(filter(None, content))
        
        if not processed_content:
            logger.warning(f"No content extracted from Obsius note: {url}")
            return None
            
        # Update document state with new content
        lines = processed_content.split('\n')
        update_document_state(
            obsius_id,
            lines=lines,
            successfully_added_to_anki=False
        )
        
        logger.info(f"Successfully scraped Obsius note: {url}")
        
        # Return content in a format compatible with the document processing system
        return {
            'content': processed_content,
            'source': 'obsius',
            'id': obsius_id,
            'version': None  # Obsius doesn't provide version info
        }
            
    except requests.Timeout:
        logger.error(f"Timeout while fetching Obsius note: {url}")
        return None
    except requests.RequestException as e:
        logger.error(f"Error fetching Obsius note: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error processing Obsius note: {str(e)}")
        return None

def parse_obsius_url(url: str) -> Dict[str, str]:
    """
    Parse Obsius URL to extract relevant information.
    
    Args:
        url (str): The URL to parse
        
    Returns:
        dict: Dictionary containing source type and ID
        
    Raises:
        ValueError: If URL format is not supported
    """
    obsius_id = extract_obsius_id(url)
    if obsius_id:
        return {'type': 'obsius', 'id': obsius_id}
    raise ValueError(f"Unsupported URL format: {url}")
