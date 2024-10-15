# process_notes_to_cards.py
import time
import requests
import json
from aqt import mw

def get_config():
    return mw.addonManager.getConfig(__name__)

def organize_and_translate_notes_with_pinyin(notes, prompt):
    """Send a request to the OpenRouter API for processing notes."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    # Get the API key from the config
    config = get_config()
    OPENROUTER_API_KEY = config.get('openrouter_api_key', '')

    if not OPENROUTER_API_KEY:
        raise ValueError("OpenRouter API key is not set in the config.")

    # Define the data payload for the API request
    data = {
        "model": "meta-llama/llama-3.1-8b-instruct:free",
        "messages": [{"role": "user", "content": prompt}],
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
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        data=json.dumps(data)
    )

    # Handle the response and return the content
    if response.status_code == 200:
        result = response.json()
        return result['choices'][0]['message']['content'].strip()  # Extract the AI-generated text (CSV output)
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None

# Placeholder processing script
def process_notes_to_cards(notes):
    """Read Mandarin notes, call OpenRouter API, and save the processed content."""
    
    # Define the prompt for OpenRouter
    prompt = (
    f"You are given a list of Mandarin vocabulary: {notes}. "
    "Your task is to clean and process the notes and extract each vocabulary word for mandarin revision, provide the English translation, and its pinyin. "
    "Format the output as a CSV where each row represents a flashcard. "
    "The first column should contain the Mandarin word, and the second column should contain the pinyin."
    "and the third column should contain its English meanings."
    "Please provide **only** the CSV data without any additional text or explanations. "
    "The CSV should look like this:\n"
    "Mandarin,Pinyin,English\n"
) 

    # Call the OpenRouter API to process the content
    cards = organize_and_translate_notes_with_pinyin(notes, prompt)

    return cards
