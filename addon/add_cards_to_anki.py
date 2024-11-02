import json
import logging
import os
import yaml
from aqt import mw
from anki.notes import Note

logger = logging.getLogger(__name__)

def load_note_type_template(note_type_name):
    """Load a note type template from the included_note_types directory."""
    logger.info(f"Looking for note type template: {note_type_name}")
    
    # Get the addon directory path
    addon_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(addon_dir, "included_note_types")
    
    # Search through all YAML files in the templates directory
    for filename in os.listdir(templates_dir):
        if filename.endswith('.yml'):
            template_path = os.path.join(templates_dir, filename)
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    template = yaml.safe_load(f)
                    if template.get('note_type') == note_type_name:
                        logger.info(f"Found matching template in {filename}")
                        return template
            except Exception as e:
                logger.error(f"Error reading template file {filename}: {e}")
                continue
    
    logger.warning(f"No template found for note type: {note_type_name}")
    return None

def initialize_note_type_from_template(template):
    """Create a new note type in Anki from a template."""
    logger.info(f"Initializing note type: {template['note_type']}")
    
    # Create a new note type
    model = mw.col.models.new(template['note_type'])
    
    # Add fields
    for field_name in template['fields']:
        field = mw.col.models.new_field(field_name)
        mw.col.models.add_field(model, field)
    
    # Add template
    template_dict = mw.col.models.new_template("Card 1")
    template_dict['qfmt'] = template['template']['front']
    template_dict['afmt'] = template['template']['back']
    mw.col.models.add_template(model, template_dict)
    
    # Add styling
    model['css'] = template['styling']
    
    # Add the model to the collection
    mw.col.models.add(model)
    mw.col.models.save(model)
    
    logger.info(f"Successfully created note type: {template['note_type']}")
    return model

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

def add_note_to_deck(deck_name, note_type_name, fields):
    """Add a new note (flashcard) to the specified deck."""
    logger.info(f"Adding note to deck '{deck_name}': Fields - {fields}")

    # Get the deck ID and note type for the note
    deck_id = check_or_create_deck(deck_name)
    note_type = mw.col.models.by_name(note_type_name)

    # If note type doesn't exist, try to create it from template
    if not note_type:
        logger.info(f"Note type '{note_type_name}' not found. Attempting to create from template...")
        template = load_note_type_template(note_type_name)
        if template:
            note_type = initialize_note_type_from_template(template)
        else:
            raise ValueError(f"Note type '{note_type_name}' not found in Anki and no template available.")

    # Create a new note
    note = Note(mw.col, note_type)
    
    # Set the fields of the note
    for i, (field_name, field_value) in enumerate(fields.items()):
        if i < len(note.fields):
            note.fields[i] = field_value
        else:
            logger.warning(f"Field '{field_name}' not found in the note type.")
    
    # Set the deck ID for the note
    note.note_type()['did'] = deck_id

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

    # Get the flashcards data using the flashcards_data key from the configuration
    flashcards_key = stage_config.get('flashcards_data', 'flashcards')
    flashcards = stage_data.get(flashcards_key, [])
    logger.debug(f"Flashcards data: {flashcards}")
    
    if isinstance(flashcards, str):
        try:
            flashcards = json.loads(flashcards)
        except json.JSONDecodeError:
            logger.error(f"Error: Invalid JSON data in flashcards: {flashcards}")
            return {"cards_added": 0, "error": "Invalid JSON data in flashcards"}
    elif not isinstance(flashcards, list):
        logger.error(f"Error: Unexpected flashcards data type: {type(flashcards)}")
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
