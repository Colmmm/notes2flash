"""Utility functions for processing notes into flashcards."""
import json
import re
import requests
from typing import List, Dict, Any, Tuple, Union
from .scrape_utils import load_config
from .logger import get_logger

logger = get_logger()

def extract_json_from_response(response_content: str, allow_partial: bool = False) -> List[Dict[str, Any]]:
    """
    Extract and parse JSON data from API response content.
    
    Args:
        response_content: The response content to parse
        allow_partial: If True, attempt to parse partial/incomplete responses by extracting complete objects
    """
    # First try to find a complete JSON array
    json_match = re.search(r'\[\s*{[^]]*}\s*\]', response_content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            logger.error("Failed to parse extracted JSON")
            if not allow_partial:
                return []
    
    # Only attempt partial parsing if explicitly allowed
    if allow_partial:
        # Try to find as many complete objects as possible
        objects = re.findall(r'{[^{}]*}(?=\s*,|\s*\])', response_content)
        if objects:
            try:
                # Reconstruct a valid JSON array from the complete objects
                reconstructed_json = f"[{','.join(objects)}]"
                logger.warning("Response appears to be truncated, attempting to parse complete objects")
                return json.loads(reconstructed_json)
            except json.JSONDecodeError:
                logger.error("Failed to parse reconstructed JSON from partial response")
                return []
    
    logger.error("No valid JSON data found in the text")
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

def call_openrouter_api(prompt: str, model: str, input_data: Dict[str, Any], is_final_step: bool, output_fields: List[str] = None) -> Union[str, List[Dict[str, Any]]]:
    """
    Send a request to the OpenRouter API for processing notes with retry logic.
    
    Args:
        prompt (str): The prompt template to use
        model (str): The model to use
        input_data (Dict[str, Any]): The input data for formatting the prompt
        is_final_step (bool): Whether this is the final step in the workflow
        output_fields (List[str], optional): Expected fields in the output JSON for final step
        
    Returns:
        Union[str, List[Dict[str, Any]]]: For intermediate steps, returns the raw response content.
                                         For the final step, returns the parsed JSON list.
        
    Raises:
        ValueError: If there's an error formatting the prompt or processing the response
        RuntimeError: If all retry attempts fail
    """
    import time
    import uuid
    from datetime import datetime
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    max_retries = 5
    retry_delay = 10  # initial retry delay is 10 seconds and then additional 2 seconds for each failed attempt
    
    # Get API key (this is required before retries since we don't want to retry auth errors)
    try:
        api_key = get_api_key_from_config()
    except Exception as e:
        logger.error(f"Failed to get API key: {str(e)}")
        raise

    # Format prompt (this is required before retries since we don't want to retry formatting errors)
    try:
        base_prompt = format_prompt_safely(prompt, input_data)
    except Exception as e:
        logger.error(f"Error formatting prompt: {str(e)}")
        raise ValueError(f"Error formatting prompt: {str(e)}")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://github.com/Colmmm/notes2flash",
        "X-Title": "Notes2Flash",
        "Content-Type": "application/json",
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache"
    }

    last_error = None
    for attempt in range(max_retries):
        # Add a unique suffix to the prompt for each retry attempt
        retry_suffix = "" if attempt == 0 else (
            f"\n\nRetry attempt {attempt} at {datetime.utcnow().isoformat()} "
            f"with nonce {uuid.uuid4()} "
            f"(Previous error: {last_error})"
        )
        formatted_prompt = base_prompt + retry_suffix
        
        logger.info("\nFormatted prompt being sent to API:\n" + "-"*80 + "\n" + formatted_prompt + "\n" + "-"*80)
        
        # Define the data payload for the API request with a unique identifier for this attempt
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": f"Request ID: {datetime.utcnow().isoformat()}-{uuid.uuid4()}-attempt{attempt}"},  # Add unique identifier
                {"role": "user", "content": formatted_prompt}
            ],
            "unique_token": str(uuid.uuid4()),  # Random token to prevent caching
            "timestamp": datetime.utcnow().isoformat(),  # Add a timestamp
            "top_p": 1,
            "temperature": 0.8,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "repetition_penalty": 1,
            "top_k": 0,
        }
        try:
            # Send the request to the API
            response = requests.post(
                url=url,
                headers=headers,
                data=json.dumps(data)
            )
            response.raise_for_status()
            
            # Parse the response
            result = response.json()
            
            # Check if the response has the expected structure
            if 'choices' not in result or not result['choices']:
                raise KeyError("Response missing 'choices' key or empty choices")
                
            if 'message' not in result['choices'][0]:
                raise KeyError("Response missing 'message' key in first choice")
                
            if 'content' not in result['choices'][0]['message']:
                raise KeyError("Response missing 'content' key in message")
            
            # Extract and log the response content
            response_content = result['choices'][0]['message']['content'].strip()
            logger.info("\nAPI Response:\n" + "-"*80 + "\n" + response_content + "\n" + "-"*80)
            
            if is_final_step:
                # Extract JSON from response for final step
                # Only allow partial parsing on the final retry attempt
                allow_partial = (attempt == max_retries - 1)
                parsed_result = extract_json_from_response(response_content, allow_partial)
                
                # Validate the parsed result
                if not parsed_result or not isinstance(parsed_result, list):
                    raise ValueError("Failed to parse JSON from final step response")
                
                # Validate output fields if specified
                if output_fields:
                    validate_output(parsed_result, output_fields)
                
                return parsed_result
            else:
                # Return raw content for intermediate steps
                return response_content
            
        except (requests.exceptions.RequestException, KeyError, ValueError, json.JSONDecodeError) as e:
            last_error = str(e)
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {last_error}")
            
            # If this wasn't our last attempt, wait before retrying
            if attempt < max_retries - 1:
                logger.info(f"For attempt {attempt + 1}/{max_retries} waiting {retry_delay} seconds...")
                time.sleep(retry_delay)
                logger.info((f"Wait for attempt {attempt + 1}/{max_retries} is over. Proceeding again."))
                retry_delay+=2 # increase wait by 2 seconds
                continue
            
            # If this was our last attempt, raise a comprehensive error
            error_msg = (
                f"All {max_retries} attempts failed. Last error: {last_error}\n\n"
                "🚨 Troubleshooting Tips:\n"
                "1. Try using a different model. Some models may not handle large inputs or complex prompts effectively.\n"
                "2. Verify that the API output is correctly formatted as a list of dictionaries. Parsing errors often occur if the response structure is not as expected.\n"
                "   - Ensure the response follows this structure:\n"
                "     [\n"
                "       {\"key1\": \"value1\", \"key2\": \"value2\"},\n"
                "       {\"key1\": \"value3\", \"key2\": \"value4\"}\n"
                "     ]\n"
                "3. Reduce the chunk size to avoid exceeding the model's context window.\n"
                "4. Check if the API is returning a cached response. You can avoid caching by adding unique identifiers (e.g., timestamps or random tokens) to your input.\n"
                "5. Beware free models typically have usage limits.\n" 
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)
