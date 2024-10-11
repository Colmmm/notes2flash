# scripts/process_content.py
import os
import time
import requests
import json

# Load API key from environment variable
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def wait_for_file(file_path):
    """Wait for a specific file to be created."""
    while not os.path.exists(file_path):
        print(f"Waiting for {file_path} to be created...")
        time.sleep(1)

def organize_and_translate_notes_with_pinyin(notes, prompt):
    """Send a request to the OpenRouter API for processing notes."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    
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
def process_content(input_file, output_file):
    """Read Mandarin notes, call OpenRouter API, and save the processed content."""
    with open(input_file, 'r') as f:
        notes = f.read()
    
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
    processed_content = organize_and_translate_notes_with_pinyin(notes, prompt)
    
    # Save the processed content to the output file
    if processed_content:
        with open(output_file, 'w') as f:
            f.write(processed_content)
        print(f"Processed content saved to {output_file}")
    else:
        print("Processing failed. No content saved.")

if __name__ == "__main__":
    # Wait for the scraping to be done
    wait_for_file('/app/output/scraping.done')

    # Processing
    input_file = "/app/output/scraped_content.txt"
    output_file = "/app/output/processed_content.txt"
    process_content(input_file, output_file)

    # After processing, delete the done file
    os.remove('/app/output/scraping.done')

    # Indicate that processing is complete
    with open('/app/output/processing.done', 'w') as f:
        f.write('Processing completed.')
