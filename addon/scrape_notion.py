import logging
from .scrape_utils import (
    load_config,
    extract_text_from_doc,
    logger
)

def scrape_notion_page(url):
    """Fetch content from a Notion page using the Notion API."""
    try:
        from notion_client import Client
        
        # Load Notion API key from config
        config = load_config()
        notion_api_key = config.get('notion_api_key')
        
        if not notion_api_key:
            raise ValueError("Notion API key not found in configuration. Please add your integration token through Anki's addon configuration.")
        
        # Initialize Notion client
        notion = Client(auth=notion_api_key)
        
        # Extract page ID from URL
        from .scrape_utils import parse_url
        source_info = parse_url(url)
        page_id = source_info['id']
        
        # Get page content
        page = notion.pages.retrieve(page_id)
        blocks = notion.blocks.children.list(page_id)
        
        content = []
        
        # Process blocks recursively
        def process_blocks(blocks):
            for block in blocks.get('results', []):
                block_type = block.get('type')
                if not block_type:
                    continue
                
                block_content = block.get(block_type)
                if not block_content:
                    continue
                
                # Handle different block types
                if block_type == 'paragraph':
                    text = ''.join(t.get('text', {}).get('content', '') 
                                 for t in block_content.get('rich_text', []))
                    if text:
                        content.append(text)
                
                elif block_type == 'heading_1':
                    text = ''.join(t.get('text', {}).get('content', '') 
                                 for t in block_content.get('rich_text', []))
                    if text:
                        content.append(f"\n# {text}\n")
                
                elif block_type == 'heading_2':
                    text = ''.join(t.get('text', {}).get('content', '') 
                                 for t in block_content.get('rich_text', []))
                    if text:
                        content.append(f"\n## {text}\n")
                
                elif block_type == 'heading_3':
                    text = ''.join(t.get('text', {}).get('content', '') 
                                 for t in block_content.get('rich_text', []))
                    if text:
                        content.append(f"\n### {text}\n")
                
                elif block_type == 'bulleted_list_item':
                    text = ''.join(t.get('text', {}).get('content', '') 
                                 for t in block_content.get('rich_text', []))
                    if text:
                        content.append(f"• {text}")
                
                elif block_type == 'numbered_list_item':
                    text = ''.join(t.get('text', {}).get('content', '') 
                                 for t in block_content.get('rich_text', []))
                    if text:
                        content.append(f"- {text}")
                
                elif block_type == 'code':
                    text = ''.join(t.get('text', {}).get('content', '') 
                                 for t in block_content.get('rich_text', []))
                    if text:
                        content.append(f"```\n{text}\n```")
                
                elif block_type == 'quote':
                    text = ''.join(t.get('text', {}).get('content', '') 
                                 for t in block_content.get('rich_text', []))
                    if text:
                        content.append(f"> {text}")
                
                # Handle nested blocks
                if block.get('has_children'):
                    child_blocks = notion.blocks.children.list(block.get('id'))
                    process_blocks(child_blocks)
        
        process_blocks(blocks)
        
        # Format content in a way compatible with Google Docs structure
        return {
            'body': {
                'content': [{'paragraph': {'elements': [{'textRun': {'content': line}}]}} 
                          for line in content if line.strip()]
            },
            'revisionId': page.get('last_edited_time')  # Use last_edited_time as revision ID
        }
    
    except ImportError:
        logger.error("notion-client is required for accessing Notion pages. Please install notion-client package.")
        raise ValueError("notion-client is required for accessing Notion pages. Please install notion-client package.")
    except Exception as e:
        logger.error(f"Failed to fetch Notion page: {str(e)}")
        raise ValueError(f"Failed to fetch Notion page. Ensure you have the correct permissions: {str(e)}")
