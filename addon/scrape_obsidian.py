import requests
import json
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse
from .scrape_utils import logger

def fetch_obsius_content(url: str) -> Optional[Dict[str, Any]]:
    """
    Fetch content from an Obsius URL.
    
    Args:
        url: The Obsius URL to fetch content from
        
    Returns:
        Optional[Dict[str, Any]]: The note content if successful, None otherwise
    """
    try:
        # Make the request
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse JSON response
        if 'application/json' in response.headers.get('Content-Type', ''):
            data = response.json()
            content = data.get("body", {}).get("post", {}).get("content", "")
            if not content:
                raise ValueError("No content found in response")
            
            # Split content into lines and format for extract_text_from_doc
            return {
                'body': {
                    'content': [{'paragraph': {'elements': [{'textRun': {'content': line}}]}} 
                              for line in content.split('\n')]
                },
                'revisionId': None  # Obsius doesn't provide revision info
            }
            
        else:
            raise ValueError("Unexpected content type; expected application/json")
            
    except requests.RequestException as e:
        logger.error(f"Failed to fetch content from {url}: {e}")
        return None
    except (ValueError, json.JSONDecodeError) as e:
        logger.error(f"Error processing content from {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error processing {url}: {e}")
        return None
