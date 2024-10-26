# process_notes_to_cards.py
import requests
import json
import logging
import re
import os

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

def process_notes_to_cards(stage_data, stage_config):
    """Process notes to cards using the provided configuration."""
    logger.info("Starting process_notes_to_cards")
    
    if not isinstance(stage_config, list) or len(stage_config) == 0:
        raise ValueError("Invalid stage_config. Expected a non-empty list.")

    # For now, we'll only handle the first processing step
    config = stage_config[0]
    
    model = config.get('model', 'meta-llama/llama-3.1-8b-instruct:free')
    prompt = config.get('prompt', '')
    input_keys = config.get('input', [])
    output_name = config.get('output', 'flashcards')
    output_fields = config.get('output_fields', [])

    if not output_fields:
        raise ValueError("No output fields specified in the configuration.")

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

    # Call the API
    try:
        result = call_openrouter_api(prompt, model, step_input)
        logger.debug(f"API result: {result}")
    except Exception as e:
        logger.error(f"Error in API call: {str(e)}")
        raise ValueError(f"Error in API call: {str(e)}")

    # Parse and validate the result
    try:
        parsed_result = extract_json_from_text(result)
        if parsed_result is None or not isinstance(parsed_result, list):
            raise ValueError("Failed to extract valid JSON list from API output")
        
        # Validate the structure of each item in the list
        for item in parsed_result:
            if not isinstance(item, dict) or not all(field in item for field in output_fields):
                raise ValueError(f"Invalid structure in API output. Expected fields: {output_fields}")
        
        logger.info("Completed process_notes_to_cards")
        logger.debug(f"Final output: {parsed_result}")
        return {output_name: parsed_result}
    except Exception as e:
        logger.error(f"Error processing API output: {str(e)}")
        raise ValueError(f"Error processing API output: {str(e)}")
