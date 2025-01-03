"""Utility functions for processing notes into flashcards."""
import json
import logging
import re
import requests
from typing import List, Dict, Any, Tuple
from .scrape_utils import load_config

logger = logging.getLogger("notes2flash")

def extract_json_from_response(response_content: str) -> List[Dict[str, Any]]:
    """Extract and parse JSON data from API response content."""
    json_match = re.search(r'\[.*\]', response_content, re.DOTALL)
    if not json_match:
        logger.error("No JSON data found in the text")
        return []
        
    try:
        return json.loads(json_match.group())
    except json.JSONDecodeError:
        logger.error("Failed to parse extracted JSON")
        return []

def get_api_key_from_config() -> str:
    """Read the OpenRouter API key from the addon's config."""
    try:
        config = load_config()
        # If its loading from config.json, the API key is a direct key
        if isinstance(config, dict) and 'openrouter_api_key' in config:
            return config['openrouter_api_key']
        # The config from meta.json has the API key under the 'config' key
        if isinstance(config, dict) and 'config' in config:
            config = config['config']
        api_key = config.get('openrouter_api_key')
        if not api_key:
            raise ValueError("OpenRouter API key not found in config")
        return api_key
    except Exception as e:
        logger.error(f"Error reading API key from config: {str(e)}")
        raise

def split_content_into_chunks(content: str, chunk_size: int) -> List[str]:
    """Split content into chunks of specified size, trying to break at sentence boundaries."""
    if len(content) <= chunk_size:
        return [content]

    chunks = []
    current_pos = 0
    content_length = len(content)

    while current_pos < content_length:
        if current_pos + chunk_size >= content_length:
            chunks.append(content[current_pos:])
            break
        
        # Find the last sentence boundary within the chunk size
        chunk_end = current_pos + chunk_size
        last_period = content.rfind('.', current_pos, chunk_end)
        last_newline = content.rfind('\n', current_pos, chunk_end)
        
        # Use the latest sentence boundary found
        split_pos = max(last_period, last_newline)
        
        if split_pos == -1 or split_pos <= current_pos:
            # If no natural boundary found, split at chunk_size
            split_pos = chunk_end
        else:
            # Include the sentence boundary character
            split_pos += 1
        
        chunks.append(content[current_pos:split_pos].strip())
        current_pos = split_pos

    return chunks

def format_prompt_safely(prompt: str, input_data: Dict[str, Any]) -> str:
    """Safely format a prompt by only replacing {variable} patterns that match input_data keys."""
    def replace_var(match):
        var_name = match.group(1)
        # Only replace if it's a variable name in our input data
        if var_name in input_data:
            return str(input_data[var_name])
        # Otherwise return the original match
        return match.group(0)
    
    # Only match {variable} patterns that aren't part of JSON
    pattern = r'(?<!["{\w])\{([^{}]+)\}(?![\w}"])'
    return re.sub(pattern, replace_var, prompt)

def validate_step_config(step_config: Dict[str, Any], step_index: int, stage_config: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate step configuration and extract key parameters."""
    validated = {
        'model': step_config.get('model', 'meta-llama/llama-3.1-8b-instruct:free'),
        'prompt': step_config.get('prompt', ''),
        'input_keys': step_config.get('input', []),
        'output_name': step_config.get('output', 'flashcards'),
        'output_fields': step_config.get('output_fields', []),
        'attach_format_reminder': step_config.get('attach_format_reminder', False),
        'chunk_size': 4000  # Default chunk size
    }
    
    try:
        validated['chunk_size'] = int(step_config.get('chunk_size', 4000))
    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid chunk_size in config, using default of 4000 chars: {str(e)}")
    
    if validated['attach_format_reminder'] and step_index == len(stage_config) - 1 and validated['output_fields']:
        validated['prompt'] += "\n" + generate_format_reminder(validated['output_fields'])
        logger.debug("Added format reminder to prompt")
    
    return validated

def prepare_step_input(input_keys: List[str], stage_data: Dict[str, Any], content_key: str, chunk: str) -> Dict[str, Any]:
    """Prepare input data for a step."""
    step_input = {}
    for key in input_keys:
        try:
            step_input[key.split('.')[-1]] = get_nested_value(stage_data, key)
        except KeyError as e:
            logger.error(f"Error preparing input: {str(e)}")
            raise ValueError(f"Required input '{key}' not found in stage data")
    
    # Add the chunk content
    step_input[content_key] = chunk
    return step_input

def validate_output(result: List[Dict[str, Any]], output_fields: List[str]) -> None:
    """Validate the structure of step output."""
    if not output_fields:
        return
        
    for item in result:
        if not isinstance(item, dict) or not all(field in item for field in output_fields):
            raise ValueError(f"Invalid structure in API output. Expected fields: {output_fields}")

def get_nested_value(data: Dict[str, Any], key_path: str) -> Any:
    """Get a nested value from a dictionary using a dot-separated key path."""
    keys = key_path.split('.')
    value = data
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            raise KeyError(f"Key '{key}' not found in nested structure")
    return value

def generate_format_reminder(output_fields: List[str]) -> str:
    """Generate a structured reminder about the expected output format."""
    # Create two example entries using output_fields
    example_entry_1 = {field: f"example_{field}_1" for field in output_fields}
    example_entry_2 = {field: f"example_{field}_2" for field in output_fields}
    
    # Convert examples to JSON strings with proper escaping
    example_json_1 = json.dumps(example_entry_1, indent=4)
    example_json_2 = json.dumps(example_entry_2, indent=4)
    
    # Create the reminder text
    reminder_text = (
        "\n**IMPORTANT**\n"
        "Format the output as a list of dictionaries, where each dictionary represents a flashcard.\n\n"
        f"Each dictionary must contain exactly these keys: {', '.join(output_fields)}.\n\n"
        "Strictly adhere to this structure. Any deviation from this format will not be accepted.\n\n"
        "Example output:\n"
        "[\n"
        f"{example_json_1},\n"
        f"{example_json_2},\n"
        "    ...\n"
        "]\n"
    )
    
    return reminder_text

def get_content_key_from_previous_step(current_step_index: int, stage_config: List[Dict[str, Any]], 
                                     workflow_config: Dict[str, Any]) -> Tuple[str, str]:
    """
    Get the content key and its source from the previous step in the workflow.
    
    Args:
        current_step_index: Index of the current step in stage_config
        stage_config: List of processing step configurations
        workflow_config: Complete workflow configuration
    
    Returns:
        Tuple of (content_key, source) where source is either 'scrape_notes' or 'process_step'
    """
    # If this is the first processing step, get content key from scrape_notes
    if current_step_index == 0:
        scrape_config = workflow_config.get('scrape_notes', [])
        if isinstance(scrape_config, list) and len(scrape_config) > 0:
            content_key = scrape_config[0].get('output')
        elif isinstance(scrape_config, dict):
            content_key = scrape_config.get('output')
        else:
            raise ValueError("Could not determine scrape_notes output key from workflow configuration")

        if not content_key:
            raise ValueError("No output key found in scrape_notes configuration")
        
        return content_key, 'scrape_notes'
    
    # Otherwise, get content key from the previous processing step
    prev_step = stage_config[current_step_index - 1]
    content_key = prev_step.get('output')
    
    if not content_key:
        raise ValueError(f"No output key found in previous processing step: {prev_step.get('step', 'unnamed')}")
    
    return content_key, 'process_step'

def call_openrouter_api(prompt: str, model: str, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Send a request to the OpenRouter API for processing notes."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    try:
        api_key = get_api_key_from_config()
    except Exception as e:
        logger.error(f"Failed to get API key: {str(e)}")
        raise

    # Format the prompt with input data using our safe formatter
    try:
        formatted_prompt = format_prompt_safely(prompt, input_data)
        # Log the formatted prompt in a more readable way
        logger.info("\nFormatted prompt being sent to API:\n" + "-"*80 + "\n" + formatted_prompt + "\n" + "-"*80)
    except Exception as e:
        logger.error(f"Error formatting prompt: {str(e)}")
        raise ValueError(f"Error formatting prompt: {str(e)}")

    # Define the data payload for the API request
    data = {
        "model": model,
        "messages": [{"role": "user", "content": formatted_prompt}],
        "top_p": 1,
        "temperature": 0.8,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "repetition_penalty": 1,
        "top_k": 0,
    }

    # Send the request to the API
    try:
        response = requests.post(
            url=url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://github.com/Colmmm/notes2flash",
                "X-Title": "Notes2Flash",
                "Content-Type": "application/json"
            },
            data=json.dumps(data)
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error in API request: {str(e)}")
        raise

    # Handle the response and return the content
    try:
        result = response.json()
        response_content = result['choices'][0]['message']['content'].strip()
        # Log the API response in a more readable way
        logger.info("\nAPI Response:\n" + "-"*80 + "\n" + response_content + "\n" + "-"*80)
        return extract_json_from_response(response_content)
    except (KeyError, IndexError) as e:
        logger.error(f"Error parsing API response: {str(e)}")
        raise ValueError(f"Unexpected API response format: {str(e)}")
