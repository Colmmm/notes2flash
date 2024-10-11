# add_cards_to_anki.py
import csv
import requests
import os
import time
from io import StringIO

ANKI_CONNECT_URL = os.getenv("ANKI_API_URL", "http://localhost:8765")

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

# main
def add_cards_to_anki(content, deck_name):
    """Process the CSV content and add each front/back pair as a note."""
    reader = csv.reader(StringIO(content))
    
    for row in reader:
        if len(row) != 3:
            print(f"Skipping invalid row: {row}")
            continue
        mandarin, pinyin, english = row
        front = mandarin
        back = f"{pinyin}\n{english}"  # Concatenate Pinyin and English for the back of the card
        add_note_to_deck(deck_name, front, back)
