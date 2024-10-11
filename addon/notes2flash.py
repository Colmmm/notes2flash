# notes2flash.py
from addon.scrape_notes import scrape_notes
from addon.process_notes_to_cards import process_notes_to_cards
from addon.add_cards_to_anki import add_cards_to_anki

def notes2flash(doc_id, deck_name):
    try:
        # Scraping step
        print("Starting scraping step...")
        notes = scrape_notes(doc_id)
        
        # Process scraped content
        print("Scraping successful. Processing content...")
        cards = process_notes_to_cards(notes)

        # Adding cards to Anki
        print("Processing complete. Adding notes to Anki...")
        add_cards_to_anki(cards, deck_name)
        
        print("Pipeline completed successfully.")
    except Exception as e:
        print(f"Error during pipeline execution: {str(e)}")
