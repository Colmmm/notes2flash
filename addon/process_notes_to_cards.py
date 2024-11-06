# process_notes_to_cards.py
import requests
import json
import logging
import re
import os
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

def get_api_key_from_config():
    """Read the OpenRouter API key from the addon's config file."""
    addon_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(addon_dir, "config.json")
    try:
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
        api_key = config.get('openrouter_api_key')
        if not api_key:
            raise ValueError("OpenRouter API key not found in config.json")
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

def call_openrouter_api(prompt, model, input_data):
    """Send a request to the OpenRouter API for processing notes."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    try:
        api_key = get_api_key_from_config()
    except Exception as e:
        logger.error(f"Failed to get API key: {str(e)}")
        raise

    # Format the prompt with input data
    try:
        formatted_prompt = prompt.format(**input_data)
    except KeyError as e:
        logger.error(f"KeyError while formatting prompt: {str(e)}")
        raise ValueError(f"Missing key in input data: {str(e)}")

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
        return result['choices'][0]['message']['content'].strip()
    except (KeyError, IndexError) as e:
        logger.error(f"Error parsing API response: {str(e)}")
        raise ValueError(f"Unexpected API response format: {str(e)}")

def extract_json_from_text(text):
    """Extract JSON data from potentially noisy text."""
    json_match = re.search(r'\[.*\]', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            logger.error("Failed to parse extracted JSON")
            return None
    else:
        logger.error("No JSON data found in the text")
        return None

def get_nested_value(data, key_path):
    """Get a nested value from a dictionary using a dot-separated key path."""
    keys = key_path.split('.')
    value = data
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            raise KeyError(f"Key '{key}' not found in nested structure")
    return value

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

def process_chunk(chunk: str, prompt: str, model: str, input_data: Dict[str, Any], content_key: str) -> List[Dict[str, Any]]:
    """Process a single chunk of content and return the parsed results."""
    try:
        # Update the content in input_data for this chunk
        chunk_input = input_data.copy()
        chunk_input[content_key] = chunk
        
        result = call_openrouter_api(prompt, model, chunk_input)
        logger.debug(f"API result for chunk:" "\n" f"{result}")
        parsed_result = extract_json_from_text(result)
        if parsed_result and isinstance(parsed_result, list):
            return parsed_result
        return []
    except Exception as e:
        logger.error(f"Error processing chunk: {str(e)}")
        return []

def generate_format_reminder(output_fields: List[str]) -> str:
    """Generate a structured reminder about the expected output format.
    
    Args:
        output_fields: List of required fields for each flashcard dictionary
        
    Returns:
        A formatted string containing the reminder and examples
    """
    # Create two example entries using output_fields
    example_entry_1 = {field: f"example_{field}_1" for field in output_fields}
    example_entry_2 = {field: f"example_{field}_2" for field in output_fields}
    
    # Convert examples to JSON strings, escape curly braces for Python formatting
    example_json_1 = json.dumps(example_entry_1, indent=4).replace("{", "{{").replace("}", "}}")
    example_json_2 = json.dumps(example_entry_2, indent=4).replace("{", "{{").replace("}", "}}")
    
    # Create the reminder text without using f-strings to avoid formatting issues
    reminder_text = (
        "\n**IMPORTANT**\n"
        "Format the output as a list of dictionaries, where each dictionary represents a flashcard.\n\n"
        f"Each dictionary must contain exactly these keys: {', '.join(output_fields)}.\n\n"
        "Strictly adhere to this structure. Any deviation from this format will not be accepted.\n\n"
        "Example output:\n"
        "[\n"
        f"    {example_json_1},\n"
        f"    {example_json_2},\n"
        "    ...\n"
        "]\n"
    )
    
    return reminder_text



def process_step(step_index: int, step_config: Dict[str, Any], stage_data: Dict[str, Any], 
                workflow_config: Dict[str, Any], stage_config: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Process a single step in the workflow."""
    logger.info(f"Processing step: {step_config.get('step', 'unnamed')}")
    
    model = step_config.get('model', 'meta-llama/llama-3.1-8b-instruct:free')
    prompt = step_config.get('prompt', '')
    input_keys = step_config.get('input', [])
    output_name = step_config.get('output', 'flashcards')
    output_fields = step_config.get('output_fields', [])
    attach_format_reminder = step_config.get('attach_format_reminder', False)
    
    try:
        chunk_size = int(step_config.get('chunk_size', 4000))
        logger.info(f"Using chunk size: {chunk_size}")
    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid chunk_size in config, using default of 4000 chars: {str(e)}")
        chunk_size = 4000

    # Get content key from previous step
    content_key, source = get_content_key_from_previous_step(step_index, stage_config, workflow_config)
    logger.debug(f"Using content key '{content_key}' from {source}")

    # Prepare input data for this step
    step_input = {}
    for key in input_keys:
        try:
            step_input[key.split('.')[-1]] = get_nested_value(stage_data, key)
        except KeyError as e:
            logger.error(f"Error preparing input: {str(e)}")
            raise ValueError(f"Required input '{key}' not found in stage data")
    
    logger.debug(f"Step input: {step_input}")

    # Remove any placeholders from the prompt that are not in step_input
    prompt = re.sub(r'\{[^}]*\}', lambda m: m.group(0) if m.group(0)[1:-1] in step_input else '', prompt)

    # Add format reminder if this is the last step and attach_format_reminder is True
    if attach_format_reminder and step_index == len(stage_config) - 1 and output_fields:
        format_reminder = generate_format_reminder(output_fields)
        # Use string concatenation instead of f-string to avoid formatting issues
        prompt = prompt + "\n" + format_reminder
        logger.debug("Added format reminder to prompt")

    # Verify content key exists in input data
    if content_key not in step_input:
        raise ValueError(f"Content key '{content_key}' not found in step input data")

    # Process content in chunks
    all_results = []
    chunks = split_content_into_chunks(step_input[content_key], chunk_size)
    
    if len(chunks) > 1:
        logger.info(f"Processing content in {len(chunks)} chunks")
    
    for i, chunk in enumerate(chunks, 1):
        if len(chunks) > 1:
            logger.info(f"Processing chunk {i} of {len(chunks)}")
        
        chunk_results = process_chunk(chunk, prompt, model, step_input, content_key)
        all_results.extend(chunk_results)

    # Validate the structure of each item if output_fields are specified
    if output_fields:
        for item in all_results:
            if not isinstance(item, dict) or not all(field in item for field in output_fields):
                raise ValueError(f"Invalid structure in API output. Expected fields: {output_fields}")
    
    logger.info(f"Completed step: {step_config.get('step', 'unnamed')}")
    logger.debug(f"Step output: {all_results}")
    return {output_name: all_results}

def process_notes_to_cards(stage_data: Dict[str, Any], stage_config: List[Dict[str, Any]], workflow_config: Dict[str, Any]) -> Dict[str, Any]:
    """Process notes to cards using the provided configuration, supporting multiple steps."""
    logger.info("Starting process_notes_to_cards")
    
    if not isinstance(stage_config, list) or len(stage_config) == 0:
        raise ValueError("Invalid stage_config. Expected a non-empty list.")

    # Initialize the processing state with the input stage data
    processing_state = stage_data.copy()
    final_output = {}

    # Process each step in sequence
    for step_index, step_config in enumerate(stage_config):
        try:
            # Process the current step
            step_result = process_step(step_index, step_config, processing_state, workflow_config, stage_config)
            
            # Update the processing state with the last step's output
            processing_state.update(step_result)
            
            # Update final output with the step's result
            final_output.update(step_result)
            
        except Exception as e:
            logger.error(f"Error processing step {step_config.get('step', 'unnamed')}: {str(e)}")
            raise

    logger.info("Completed process_notes_to_cards")
    logger.debug(f"Final output: {final_output}")
    return final_output
