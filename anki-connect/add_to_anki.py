import csv
import requests
import os

ANKI_CONNECT_URL = os.getenv("ANKI_API_URL")
DECK_NAME = os.getenv("ANKI_DECK_NAME", "test_deck")
PROCESSED_FILE = "/app/output/processed_content.txt"


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
            if len(row) != 2:
                print(f"Skipping invalid row: {row}")
                continue
            front, back = row
            add_note_to_deck(deck_name, front, back)

if __name__ == '__main__':
    # Check or create the deck
    check_or_create_deck(DECK_NAME)

    # Add notes from the processed content CSV file
    process_and_add_notes(PROCESSED_FILE, DECK_NAME)
