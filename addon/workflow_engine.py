import os, sys
# Add the path to the `libs` directory where extra packages are bundled
addon_folder = os.path.dirname(__file__)
libs_path = os.path.join(addon_folder, "libs")
if libs_path not in sys.path:
    sys.path.insert(0, libs_path)

import yaml
from .scrape_notes import scrape_notes
from .process_notes_to_cards import process_notes_to_cards
from .add_cards_to_anki import add_cards_to_anki

class WorkflowEngine:
    def __init__(self, workflow_config, user_inputs):
        self.workflow_config = workflow_config
        self.user_inputs = user_inputs
        self.stage_data = {}

    @staticmethod
    def load_workflow_config(config_path):
        with open(config_path, 'r') as config_file:
            config = yaml.safe_load(config_file)
        WorkflowEngine.validate_config(config)
        return config

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

    def execute_workflow_stage(self, stage_name, stage_config, progress_callback=None):
        if progress_callback:
            progress_callback(f"Starting stage: {stage_name}")

        if stage_name == "scrape_notes":
            result = scrape_notes(stage_config)
        elif stage_name == "process_notes_to_cards":
            result = process_notes_to_cards(self.stage_data, stage_config)
        elif stage_name == "add_cards_to_anki":
            result = add_cards_to_anki(self.stage_data, stage_config)
        else:
            raise ValueError(f"Unknown stage: {stage_name}")

        if progress_callback:
            progress_callback(f"Completed stage: {stage_name}")

        return result

    def run_workflow(self, progress_callback=None):
        try:
            self.stage_data.update(self.user_inputs)

            for stage in self.workflow_config['stages']:
                if progress_callback:
                    progress_callback(f"Preparing stage: {stage}")

                stage_config = self.workflow_config.get(stage, {})
                stage_result = self.execute_workflow_stage(stage, stage_config, progress_callback)

                if isinstance(stage_result, dict):
                    self.stage_data.update(stage_result)
                else:
                    self.stage_data[stage] = stage_result

            if progress_callback:
                progress_callback("Workflow completed successfully")

            return True
        except Exception as e:
            error_message = f"Error in workflow execution: {str(e)}"
            if progress_callback:
                progress_callback(error_message)
            raise RuntimeError(error_message)

    def get_final_result(self):
        return self.stage_data
