import json
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

def add_note_to_deck(deck_name, model_name, fields):
    """Add a new note (flashcard) to the specified deck."""
    print(f"Adding note to deck '{deck_name}': Fields - {fields}")

    # Get the deck ID and model for the note
    deck_id = check_or_create_deck(deck_name)
    model = mw.col.models.byName(model_name)

    if not model:
        raise ValueError(f"Model '{model_name}' not found in Anki.")

    # Create a new note
    note = Note(mw.col, model)
    
    # Set the fields of the note
    for i, (field_name, field_value) in enumerate(fields.items()):
        if i < len(note.fields):
            note.fields[i] = field_value
        else:
            print(f"Warning: Field '{field_name}' not found in the note model.")
    
    # Set the deck ID for the note
    note.model()['did'] = deck_id

    # Add the note to the collection
    if mw.col.addNote(note):
        print(f"Note added to deck '{deck_name}': Fields - {fields}")
    else:
        print(f"Failed to add note to deck '{deck_name}'.")

def add_cards_to_anki(stage_data, stage_config):
    """Process the stage data and add cards to Anki based on the configuration."""
    print("Starting to add cards to Anki...")

    deck_name = stage_config.get('deck_name', 'Default')
    card_template = stage_config.get('card_template', {})
    template_name = card_template.get('template_name', 'Basic')

    # Ensure the deck exists
    check_or_create_deck(deck_name)

    # Get the flashcards data
    flashcards_data = stage_data.get('flashcards', '[]')
    
    try:
        flashcards = json.loads(flashcards_data)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON data in flashcards: {flashcards_data}")
        return

    cards_added = 0
    # Process each flashcard and add it to the deck
    for card_data in flashcards:
        fields = {}
        for field, template in card_template.items():
            if field != 'template_name':
                fields[field] = template.format(**card_data)
        
        try:
            add_note_to_deck(deck_name, template_name, fields)
            cards_added += 1
        except ValueError as e:
            print(f"Error adding card: {e}")

    print(f"Finished adding cards to Anki. {cards_added} cards added.")

    return {"cards_added": cards_added}
