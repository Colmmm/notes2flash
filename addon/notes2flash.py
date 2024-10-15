import os
from .scrape_notes import scrape_notes
from .process_notes_to_cards import process_notes_to_cards
from .add_cards_to_anki import add_cards_to_anki

def notes2flash(google_doc_id, deck_name, progress_callback=None):
    try:
        if progress_callback:
            progress_callback("Scraping Google Doc...")
        notes = scrape_notes(google_doc_id)

        if progress_callback:
            progress_callback("Processing notes...")
        cards = process_notes_to_cards(notes)

        if progress_callback:
            progress_callback("Creating Anki cards...")
        add_cards_to_anki(cards, deck_name)

        if progress_callback:
            progress_callback("Uploading to Anki...")
        
        return True
    except Exception as e:
        if progress_callback:
            progress_callback(f"Error: {str(e)}")
        raise e

# Keep any other existing functions in this file
