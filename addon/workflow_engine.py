import os, sys
# Add the path to the `libs` directory where extra packages are bundled
addon_folder = os.path.dirname(__file__)
libs_path = os.path.join(addon_folder, "libs")
if libs_path not in sys.path:
    sys.path.insert(0, libs_path)

import yaml
from .scrape_notes import scrape_notes, mark_document_as_processed, get_document_state, update_document_state
from .process_notes_to_cards import process_notes_to_cards
from .add_cards_to_anki import add_cards_to_anki
from .scrape_utils import parse_url
from .logger import get_logger, reinitialize_logger

# Get logger instance
logger = get_logger()

class WorkflowEngine:
    def __init__(self, workflow_config, user_inputs, debug=False):
        self.workflow_config = workflow_config
        self.user_inputs = user_inputs
        self.stage_data = {}
        self.debug = debug
        if self.debug:
            logger = reinitialize_logger(debug=True)
        else:
            logger = reinitialize_logger(debug=False)

    @staticmethod
    def load_workflow_config(config_path):
        try:
            with open(config_path, 'r') as config_file:
                config = yaml.safe_load(config_file)
            WorkflowEngine.validate_config(config)
            return config
        except Exception as e:
            logger.error(f"Error loading workflow config: {str(e)}")
            raise

    @staticmethod
    def validate_config(config):
        required_keys = ['workflow_name', 'user_inputs', 'scrape_notes', 'process_notes_to_cards', 'add_cards_to_anki']
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing required key in workflow config: {key}")

        if not isinstance(config['user_inputs'], list) or len(config['user_inputs']) == 0:
            raise ValueError("'user_inputs' must be a non-empty list")

        if not isinstance(config['scrape_notes'], list) and not isinstance(config['scrape_notes'], dict):
            raise ValueError("'scrape_notes' must be a list or a dictionary")

        if not isinstance(config['process_notes_to_cards'], list):
            raise ValueError("'process_notes_to_cards' must be a list")

        if not isinstance(config['add_cards_to_anki'], dict):
            raise ValueError("'add_cards_to_anki' must be a dictionary")

    def replace_placeholders(self, config, data, stage_name=None):
        """Replace placeholders in the config with values from the user inputs."""
        if isinstance(config, dict):
            # For process_notes_to_cards stage, skip replacing placeholders in prompts
            if stage_name == "process_notes_to_cards" and "prompt" in config:
                return {k: (v if k == "prompt" else self.replace_placeholders(v, data, stage_name)) for k, v in config.items()}
            return {k: self.replace_placeholders(v, data, stage_name) for k, v in config.items()}
        elif isinstance(config, list):
            # For process_notes_to_cards stage, handle each step's config
            if stage_name == "process_notes_to_cards":
                return [self.replace_placeholders(item, data, stage_name) for item in config]
            return [self.replace_placeholders(item, data, stage_name) for item in config]
        elif isinstance(config, str) and '{' in config and '}' in config:
            try:
                return config.format(**data)
            except KeyError as e:
                logger.warning(f"KeyError while replacing placeholders: {str(e)}")
                return config  # Return the original string if placeholder replacement fails
        else:
            return config

    def execute_workflow_stage(self, stage_name, stage_config, progress_callback=None):
        logger.info(f"Starting stage: {stage_name}")
        if progress_callback:
            progress_callback(f"Starting stage: {stage_name}")

        try:
            # Replace placeholders in the stage config using user_inputs and previous stage data
            stage_config = self.replace_placeholders(stage_config, self.stage_data, stage_name)
            logger.debug(f"Stage config for {stage_name}: {stage_config}")

            if stage_name == "scrape_notes":
                result = scrape_notes(stage_config)
                output_name = stage_config[0].get('output', 'scraped_notes_output') if isinstance(stage_config, list) else stage_config.get('output', 'scraped_notes_output')
                self.stage_data[output_name] = result[output_name]
                
                # Parse URL to get doc_id and source type
                url = stage_config[0].get('url') if isinstance(stage_config, list) else stage_config.get('url')
                if url:
                    source_info = parse_url(url)
                    self.stage_data['doc_id'] = source_info['id']
                    self.stage_data['source_type'] = source_info['type']
                    self.stage_data['source_url'] = url
            elif stage_name == "process_notes_to_cards":
                if not isinstance(stage_config, list) or len(stage_config) == 0:
                    raise ValueError("Invalid stage_config for process_notes_to_cards. Expected a non-empty list.")
                logger.debug(f"Input data for process_notes_to_cards: {self.stage_data}")
                result = process_notes_to_cards(self.stage_data, stage_config, self.workflow_config)
                logger.debug(f"Output from process_notes_to_cards: {result}")
                self.stage_data.update(result)  # This will add the 'flashcards' key to stage_data
            elif stage_name == "add_cards_to_anki":
                if not isinstance(stage_config, dict):
                    raise ValueError("Invalid stage_config for add_cards_to_anki. Expected a dictionary.")
                result = add_cards_to_anki(self.stage_data, stage_config)
                # Check for actual errors, but don't treat duplicates as errors
                if result.get('errors'):
                    error_msg = f"Failed to add some cards to Anki: {result.get('errors')}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                # Log duplicates as info, not as errors
                if result.get('duplicates', 0) > 0:
                    logger.info(f"Found {result['duplicates']} duplicate cards in deck")
            else:
                raise ValueError(f"Unknown stage: {stage_name}")

            logger.info(f"Completed stage: {stage_name}")
            if progress_callback:
                progress_callback(f"Completed stage: {stage_name}")

            return result
        except Exception as e:
            logger.error(f"Error in stage {stage_name}: {str(e)}")
            
            # If there's an error in a stage after scrape_notes, preserve the pending changes
            if stage_name != "scrape_notes":
                doc_id = self.stage_data.get('doc_id')
                if doc_id:
                    doc_state = get_document_state(doc_id)
                    # Keep the pending changes but mark as not processed
                    update_document_state(
                        doc_id,
                        doc_state['lines'],
                        doc_state['version'],
                        False,
                        doc_state.get('pending_changes', []),
                        self.stage_data.get('source_url'),
                        self.stage_data.get('source_type')
                    )
            
            raise

    def run_workflow(self, progress_callback=None):
        try:
            self.stage_data.update(self.user_inputs)
            logger.debug(f"Initial stage data: {self.stage_data}")

            stages = ['scrape_notes', 'process_notes_to_cards', 'add_cards_to_anki']
            for stage in stages:
                logger.info(f"Preparing stage: {stage}")
                if progress_callback:
                    progress_callback(f"Preparing stage: {stage}")

                stage_config = self.workflow_config.get(stage, {})
                stage_result = self.execute_workflow_stage(stage, stage_config, progress_callback)

                if isinstance(stage_result, dict):
                    self.stage_data.update(stage_result)
                elif stage_result is not None:
                    self.stage_data[stage] = stage_result

                logger.debug(f"Stage data after {stage}: {self.stage_data}")

            # After successful completion of all stages, mark the document as successfully processed
            doc_id = self.stage_data.get('doc_id')
            logger.debug(f"Document ID for marking as processed: {doc_id}")
            if doc_id:
                # Consider the document processed if we either added cards or found duplicates
                cards_added = self.stage_data.get('cards_added', 0)
                duplicates = self.stage_data.get('duplicates', 0)
                if cards_added > 0 or duplicates > 0:
                    mark_document_as_processed(doc_id)  # This will also clear pending changes
                    logger.info(f"Marked document {doc_id} as successfully processed: {cards_added} cards added, {duplicates} duplicates found")
                else:
                    logger.warning(f"No cards were added or found as duplicates for document {doc_id}, not marking as processed")

            logger.info("Workflow completed successfully")
            if progress_callback:
                progress_callback("Workflow completed successfully")

            return True
        except Exception as e:
            error_message = f"Error in workflow execution: {str(e)}"
            logger.error(error_message)
            if progress_callback:
                progress_callback(error_message)
            raise RuntimeError(error_message)

    def get_final_result(self):
        return self.stage_data
