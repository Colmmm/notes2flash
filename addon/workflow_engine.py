import os, sys
import logging
# Add the path to the `libs` directory where extra packages are bundled
addon_folder = os.path.dirname(__file__)
libs_path = os.path.join(addon_folder, "libs")
if libs_path not in sys.path:
    sys.path.insert(0, libs_path)

import yaml
from .scrape_notes import scrape_notes
from .process_notes_to_cards import process_notes_to_cards
from .add_cards_to_anki import add_cards_to_anki

# Set up logging
logging.basicConfig(level=logging.DEBUG, filename='notes2flash.log', filemode='w',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WorkflowEngine:
    def __init__(self, workflow_config, user_inputs, debug=False):
        self.workflow_config = workflow_config
        self.user_inputs = user_inputs
        self.stage_data = {}
        self.debug = debug
        if self.debug:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

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
        required_keys = ['workflow_name', 'stages', 'user_inputs']
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing required key in workflow config: {key}")

        if not isinstance(config['stages'], list) or len(config['stages']) == 0:
            raise ValueError("'stages' must be a non-empty list")

        if not isinstance(config['user_inputs'], list) or len(config['user_inputs']) == 0:
            raise ValueError("'user_inputs' must be a non-empty list")

        for stage in config['stages']:
            if stage not in config:
                raise ValueError(f"Missing configuration for stage: {stage}")
            
        if 'process_notes_to_cards' in config:
            if 'steps' not in config['process_notes_to_cards']:
                raise ValueError("Missing 'steps' in process_notes_to_cards configuration")
            for step in config['process_notes_to_cards']['steps']:
                if 'name' not in step or 'prompt' not in step or 'input' not in step or 'output' not in step:
                    raise ValueError(f"Invalid step configuration in process_notes_to_cards: {step}")

    def replace_placeholders(self, config, data):
        """Replace placeholders in the config with values from the user inputs."""
        if isinstance(config, dict):
            return {k: self.replace_placeholders(v, data) for k, v in config.items()}
        elif isinstance(config, list):
            return [self.replace_placeholders(item, data) for item in config]
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
            stage_config = self.replace_placeholders(stage_config, self.stage_data)
            logger.debug(f"Stage config for {stage_name}: {stage_config}")

            if stage_name == "scrape_notes":
                result = scrape_notes(stage_config)
                output_name = stage_config.get('output', {}).get('name', 'scrape_notes_output')
                self.stage_data[output_name] = result
            elif stage_name == "process_notes_to_cards":
                logger.debug(f"Input data for process_notes_to_cards: {self.stage_data}")
                result = process_notes_to_cards(self.stage_data, stage_config)
                logger.debug(f"Output from process_notes_to_cards: {result}")
                self.stage_data.update(result)
            elif stage_name == "add_cards_to_anki":
                result = add_cards_to_anki(self.stage_data, stage_config)
            else:
                raise ValueError(f"Unknown stage: {stage_name}")

            logger.info(f"Completed stage: {stage_name}")
            if progress_callback:
                progress_callback(f"Completed stage: {stage_name}")

            return result
        except Exception as e:
            logger.error(f"Error in stage {stage_name}: {str(e)}")
            raise

    def run_workflow(self, progress_callback=None):
        try:
            self.stage_data.update(self.user_inputs)
            logger.debug(f"Initial stage data: {self.stage_data}")

            for stage in self.workflow_config['stages']:
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