# process_notes_to_cards.py
import requests
import json

def call_openrouter_api(prompt, api_key, model, input_data):
    """Send a request to the OpenRouter API for processing notes."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    if not api_key:
        raise ValueError("OpenRouter API key is not provided in the stage_config.")

    # Format the prompt with input data
    formatted_prompt = prompt.format(**input_data)

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
    response = requests.post(
        url=url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        data=json.dumps(data)
    )

    # Handle the response and return the content
    if response.status_code == 200:
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None

def process_notes_to_cards(stage_data, stage_config):
    """Process notes to cards using the provided multi-step configuration."""
    api_key = stage_config.get('api_key', '')
    steps = stage_config.get('steps', [])
    
    # Initialize the data dictionary with the input stage_data
    data = stage_data.copy()

    for step in steps:
        name = step.get('name', 'Unnamed Step')
        prompt = step.get('prompt', '')
        model = step.get('model', 'meta-llama/llama-3.1-8b-instruct:free')
        input_keys = step.get('input', [])
        output_key = step.get('output', '')

        print(f"Executing step: {name}")

        # Prepare input data for this step
        step_input = {key: data.get(key, '') for key in input_keys}

        # Call the API
        result = call_openrouter_api(prompt, api_key, model, step_input)

        # Store the result
        if result:
            data[output_key] = result
        else:
            print(f"Step '{name}' failed to produce output.")

    # Prepare the final output
    final_output = {}
    for key in stage_config.get('final_output_key_names', []):
        if key in data:
            final_output[key] = data[key]
        else:
            print(f"Warning: Expected output key '{key}' not found in processed data.")

    return final_output
