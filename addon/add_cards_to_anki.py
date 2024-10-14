import csv
from io import StringIO
from aqt import mw
from anki.notes import Note

def check_or_create_deck(deck_name):
    """Check if the deck exists in Anki, if not, create it."""
    print(f"Checking if deck '{deck_name}' exists...")

    # Get the deck ID, or create the deck if it doesn't exist
    deck_id = mw.col.decks.id(deck_name)  # Creates the deck if not found
    mw.col.decks.select(deck_id)
    
    if deck_id:
        print(f"Deck '{deck_name}' exists with ID: {deck_id}")
    else:
        print(f"Deck '{deck_name}' does not exist. Creating deck '{deck_name}'.")

    return deck_id

def add_note_to_deck(deck_name, front, back):
    """Add a new note (flashcard) to the specified deck."""
    print(f"Adding note to deck '{deck_name}': Front - '{front}', Back - '{back}'")

    # Get the deck ID and model for the note
    deck_id = check_or_create_deck(deck_name)
    model = mw.col.models.byName("Basic")  # Assuming you're using the Basic model

    # Create a new note
    note = Note(mw.col, model)
    note.fields[0] = front  # Front field
    note.fields[1] = back   # Back field
    
    # Set the deck ID for the note
    note.model()['did'] = deck_id

    # Add the note to the collection
    if mw.col.addNote(note):
        print(f"Note added to deck '{deck_name}': Front - '{front}', Back - '{back}'")
    else:
        print(f"Failed to add note to deck '{deck_name}'.")

def add_cards_to_anki(content, deck_name):
    """Process the CSV content and add each front/back pair as a note."""
    print(f"Starting to add cards to deck '{deck_name}'...")

    # Ensure the deck exists
    check_or_create_deck(deck_name)

    # Parse the CSV content
    reader = csv.reader(StringIO(content))

    # Process each row and add the notes to the deck
    for row in reader:
        print(f"Processing row: {row}")
        if len(row) != 3:
            print(f"Skipping invalid row: {row}")
            continue

        mandarin, pinyin, english = row
        front = mandarin
        back = f"{pinyin}\n{english}"  # Concatenate Pinyin and English for the back of the card
        add_note_to_deck(deck_name, front, back)

    print("Finished adding cards to Anki.")


