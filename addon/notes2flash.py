# notes2flash.py
from .scrape_notes import scrape_notes
from .process_notes_to_cards import process_notes_to_cards
from .add_cards_to_anki import add_cards_to_anki

def notes2flash(doc_id, deck_name):
    try:
        # Scraping step
        print("Starting scraping step...")
        notes = scrape_notes(doc_id)
        print("Preview of the notes:\n", notes)
        
        # Process scraped content
        print("Scraping successful. Processing content...")
        cards = process_notes_to_cards(notes)
        print("Preview of the cards:\n", cards)

        # Adding cards to Anki
        print("Processing complete. Adding notes to Anki...")
        add_cards_to_anki(cards, deck_name) 
        
        print("Pipeline completed successfully.")
    except Exception as e:
        print(f"Error during pipeline execution: {str(e)}")
