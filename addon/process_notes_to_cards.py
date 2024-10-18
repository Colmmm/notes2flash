# process_notes_to_cards.py
import requests
import json
import logging
import re

logger = logging.getLogger(__name__)

def call_openrouter_api(prompt, api_key, model, input_data):
    """Send a request to the OpenRouter API for processing notes."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    if not api_key:
        logger.error("OpenRouter API key is not provided in the stage_config.")
        raise ValueError("OpenRouter API key is not provided in the stage_config.")

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
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
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
    """Process notes to cards using the provided multi-step configuration."""
    logger.info("Starting process_notes_to_cards")
    api_key = stage_config.get('api_key', '')
    steps = stage_config.get('steps', [])
    
    # Initialize the data dictionary with the input stage_data
    data = stage_data.copy()
    logger.debug(f"Initial data: {data}")

    for step in steps:
        name = step.get('name', 'Unnamed Step')
        prompt = step.get('prompt', '')
        model = step.get('model', 'meta-llama/llama-3.1-8b-instruct:free')
        input_keys = step.get('input', [])
        output_config = step.get('output', {})

        logger.info(f"Executing step: {name}")

        # Prepare input data for this step
        step_input = {}
        for key in input_keys:
            try:
                step_input[key.split('.')[-1]] = get_nested_value(data, key)
            except KeyError as e:
                logger.error(f"Error preparing input for step '{name}': {str(e)}")
                raise ValueError(f"Required input '{key}' not found for step '{name}'")
        
        logger.debug(f"Step input for '{name}': {step_input}")

        # Call the API
        try:
            result = call_openrouter_api(prompt, api_key, model, step_input)
            logger.debug(f"API result for '{name}': {result}")
        except Exception as e:
            logger.error(f"Error in API call for step '{name}': {str(e)}")
            raise ValueError(f"Error in step '{name}': {str(e)}")

        # Parse and store the result
        try:
            parsed_result = extract_json_from_text(result)
            if parsed_result is None:
                raise ValueError(f"Failed to extract valid JSON from step '{name}' output")
            
            output_name = output_config.get('name', 'unnamed_output')
            output_keys = output_config.get('keys', [])
            
            data[output_name] = {key: parsed_result.get(key) for key in output_keys}
            logger.debug(f"Updated data after step '{name}': {data}")
        except Exception as e:
            logger.error(f"Error processing output from step '{name}': {str(e)}")
            raise ValueError(f"Error processing output from step '{name}': {str(e)}")

    # Prepare the final output
    final_output = {}
    final_step_output = data.get(steps[-1]['output']['name'], {})
    final_output_key = steps[-1]['output']['keys'][0]  # Assuming the last step's first key is the final output
    
    if final_output_key in final_step_output:
        final_output[final_output_key] = final_step_output[final_output_key]
    else:
        logger.error(f"Expected output key '{final_output_key}' not found in final step output")
        raise ValueError(f"Expected output key '{final_output_key}' not found in final step output")

    logger.info("Completed process_notes_to_cards")
    logger.debug(f"Final output: {final_output}")
    return final_output
