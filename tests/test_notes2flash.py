import pytest
from pytest_anki import AnkiSession
import json
import os

def test_addon_loads(anki_session: AnkiSession):
    """Test that the notes2flash add-on loads successfully."""
    with anki_session.profile_loaded():
        addon = anki_session.load_addon("notes2flash")
        assert addon is not None

def test_workflow_config_loads(anki_session: AnkiSession, workflow_config):
    """Test that workflow config loads successfully."""
    with anki_session.profile_loaded():
        addon = anki_session.load_addon("notes2flash")
        from notes2flash.workflow_engine import WorkflowEngine
        
        engine = WorkflowEngine()
        config = engine.load_workflow_config(workflow_config)
        
        assert config is not None
        assert "workflow_name" in config
        assert "user_inputs" in config
        assert "url" in config["user_inputs"]
        assert "deckname" in config["user_inputs"]
        assert "scrape_notes" in config
        assert "process_notes_to_cards" in config
        assert "add_cards_to_anki" in config

def test_api_keys_configured():
    """Test that API keys are properly configured."""
    config_path = os.path.join("addon", "config.json")
    assert os.path.exists(config_path), "config.json not found"
    
    with open(config_path) as f:
        config = json.load(f)
    
    assert "openrouter_api_key" in config, "openrouter_api_key missing from config"
    assert "notion_api_key" in config, "notion_api_key missing from config"
    assert len(config["openrouter_api_key"]) > 0, "openrouter_api_key is empty"
    assert len(config["notion_api_key"]) > 0, "notion_api_key is empty"

def test_workflow_execution(anki_session: AnkiSession, workflow_config, source_config):
    """Test complete workflow execution with different sources."""
    with anki_session.profile_loaded():
        addon = anki_session.load_addon("notes2flash")
        from notes2flash.notes2flash import notes2flash
        
        # Set up user inputs from source config
        user_inputs = {
            "url": source_config["url"],
            "deckname": source_config["deckname"]
        }
        
        # Run workflow
        try:
            result = notes2flash(workflow_config, user_inputs)
        except Exception as e:
            pytest.fail(f"Workflow execution failed for {source_config['source_type']}: {str(e)}")
        
        assert result is not None, f"Workflow returned None for {source_config['source_type']}"

        # Verify deck was created
        collection = anki_session.collection
        deck = collection.decks.by_name(user_inputs["deckname"])
        assert deck is not None, f"Deck '{user_inputs['deckname']}' not created"

        # Verify cards were added
        card_count = collection.card_count()
        assert card_count > 0, f"No cards added for {source_config['source_type']}"

        # Verify card fields
        cards = collection.find_cards("")
        assert len(cards) > 0, f"No cards found for {source_config['source_type']}"
        
        for card_id in cards:
            card = collection.get_card(card_id)
            note = card.note()
            
            # Check required fields exist and are not empty
            required_fields = ["mandarin", "pinyin", "translation"]
            for field in required_fields:
                assert field in note.fields, f"Field '{field}' missing from note"
                assert len(note[field]) > 0, f"Field '{field}' is empty"

def test_invalid_workflow_config(anki_session: AnkiSession):
    """Test handling of invalid workflow config."""
    with anki_session.profile_loaded():
        addon = anki_session.load_addon("notes2flash")
        from notes2flash.workflow_engine import WorkflowEngine
        
        engine = WorkflowEngine()
        
        with pytest.raises(Exception):
            engine.load_workflow_config("nonexistent_config.yml")

def test_invalid_url(anki_session: AnkiSession, workflow_config):
    """Test handling of invalid URL."""
    with anki_session.profile_loaded():
        addon = anki_session.load_addon("notes2flash")
        from notes2flash.notes2flash import notes2flash
        
        user_inputs = {
            "url": "https://invalid-url-that-doesnt-exist.com",
            "deckname": "Test Invalid URL Deck"
        }
        
        with pytest.raises(Exception):
            notes2flash(workflow_config, user_inputs)
