import csv
import requests
import os
import time

ANKI_CONNECT_URL = os.getenv("ANKI_API_URL", "http://anki-desktop:8765")
DECK_NAME = os.getenv("ANKI_DECK_NAME", "test_deck")
PROCESSED_FILE = "/app/output/processed_content.txt"

def wait_for_file(file_path):
    """Wait for a specific file to be created."""
    while not os.path.exists(file_path):
        print(f"Waiting for {file_path} to be created...")
        time.sleep(1)

def wait_for_anki():
    """Wait for the Anki Connect API to be available."""
    while True:
        try:
            response = requests.get(ANKI_CONNECT_URL)
            if response.status_code == 200:
                print(f"Anki Connect API is ready at {ANKI_CONNECT_URL}.")
                break
        except requests.exceptions.RequestException:
            print("Waiting for Anki Connect API to be available...")
        time.sleep(1)

def invoke(action, params):
    """Helper function to interact with Anki Connect API."""
    return requests.post(ANKI_CONNECT_URL, json={
        "action": action,
        "version": 6,
        "params": params
    }).json()

def check_or_create_deck(deck_name):
    """Check if the deck exists in Anki, if not, create it."""
    existing_decks = invoke('deckNames', {})['result']
    
    if deck_name not in existing_decks:
        print(f"Deck '{deck_name}' not found. Creating new deck.")
        invoke('createDeck', {"deck": deck_name})
    else:
        print(f"Deck '{deck_name}' already exists.")

def add_note_to_deck(deck_name, front, back):
    """Add a new note (flashcard) to the specified deck."""
    note = {
        "deckName": deck_name,
        "modelName": "Basic",
        "fields": {
            "Front": front,
            "Back": back
        },
        "options": {
            "allowDuplicate": False
        },
        "tags": []
    }
    response = invoke('addNote', {"note": note})
    if response.get('error'):
        print(f"Error adding note: {response['error']}")
    else:
        print(f"Added note to {deck_name}: Front - '{front}', Back - '{back}'")

def process_and_add_notes(file_path, deck_name):
    """Process the CSV file and add each front/back pair as a note."""
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) != 3:
                print(f"Skipping invalid row: {row}")
                continue
            mandarin, pinyin, english = row
            front = mandarin
            back = f"{pinyin}\n{english}"  # Concatenate Pinyin and English for the back of the card
            add_note_to_deck(deck_name, front, back)

if __name__ == '__main__':
    # Wait for processing to be done
    wait_for_file('/app/output/processing.done')

    # Wait for the Anki Connect API to be available
    wait_for_anki()

    # Check or create the deck
    check_or_create_deck(DECK_NAME)

    # Add notes from the processed content CSV file
    process_and_add_notes(PROCESSED_FILE, DECK_NAME)

    # After uploading notes, delete the done file
    os.remove('/app/output/processing.done')
