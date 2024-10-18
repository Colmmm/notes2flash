import json
import logging
from aqt import mw
from anki.notes import Note

logger = logging.getLogger(__name__)

def check_or_create_deck(deck_name):
    """Check if the deck exists in Anki, if not, create it."""
    logger.info(f"Checking if deck '{deck_name}' exists...")

    # Get the deck ID, or create the deck if it doesn't exist
    deck_id = mw.col.decks.id(deck_name)  # Creates the deck if not found
    mw.col.decks.select(deck_id)
    
    if deck_id:
        logger.info(f"Deck '{deck_name}' exists with ID: {deck_id}")
    else:
        logger.info(f"Deck '{deck_name}' does not exist. Creating deck '{deck_name}'.")

    return deck_id

def add_note_to_deck(deck_name, model_name, fields):
    """Add a new note (flashcard) to the specified deck."""
    logger.info(f"Adding note to deck '{deck_name}': Fields - {fields}")

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
            logger.warning(f"Field '{field_name}' not found in the note model.")
    
    # Set the deck ID for the note
    note.model()['did'] = deck_id

    # Add the note to the collection
    if mw.col.addNote(note):
        logger.info(f"Note added to deck '{deck_name}': Fields - {fields}")
        return True
    else:
        logger.error(f"Failed to add note to deck '{deck_name}'.")
        return False

def add_cards_to_anki(stage_data, stage_config):
    """Process the stage data and add cards to Anki based on the configuration."""
    logger.info("Starting to add cards to Anki...")
    logger.debug(f"Stage data: {stage_data}")
    logger.debug(f"Stage config: {stage_config}")

    deck_name = stage_config.get('deck_name')
    if not deck_name:
        logger.error("Deck name not provided in stage_config")
        return {"cards_added": 0, "error": "Deck name not provided"}

    card_template = stage_config.get('card_template', {})
    template_name = card_template.get('template_name', 'Basic')

    # Ensure the deck exists
    check_or_create_deck(deck_name)

    # Get the flashcards data
    flashcards_data = stage_data.get('flashcards_output', {}).get('flashcards', [])
    logger.debug(f"Flashcards data: {flashcards_data}")
    
    if isinstance(flashcards_data, str):
        try:
            flashcards = json.loads(flashcards_data)
        except json.JSONDecodeError:
            logger.error(f"Error: Invalid JSON data in flashcards: {flashcards_data}")
            return {"cards_added": 0, "error": "Invalid JSON data in flashcards"}
    elif isinstance(flashcards_data, list):
        flashcards = flashcards_data
    else:
        logger.error(f"Error: Unexpected flashcards data type: {type(flashcards_data)}")
        return {"cards_added": 0, "error": "Unexpected flashcards data type"}

    cards_added = 0
    errors = []

    # Process each flashcard and add it to the deck
    for card_data in flashcards:
        fields = {}
        try:
            for field, template in card_template.items():
                if field != 'template_name':
                    fields[field] = template.format(**card_data)
            
            if add_note_to_deck(deck_name, template_name, fields):
                cards_added += 1
            else:
                errors.append(f"Failed to add card: {card_data}")
        except KeyError as e:
            logger.error(f"Missing key in card data: {e}")
            errors.append(f"Missing key in card data: {e}")
        except ValueError as e:
            logger.error(f"Error adding card: {e}")
            errors.append(f"Error adding card: {e}")

    logger.info(f"Finished adding cards to Anki. {cards_added} cards added.")
    if errors:
        logger.warning(f"Encountered {len(errors)} errors while adding cards.")

    return {
        "cards_added": cards_added,
        "errors": errors if errors else None
    }
