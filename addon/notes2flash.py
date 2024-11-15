import logging
import os
from .workflow_engine import WorkflowEngine

# Set up logging
addon_folder = os.path.dirname(__file__)
log_file = os.path.join(addon_folder, "notes2flash.log")
logging.basicConfig(level=logging.INFO, filename=log_file, filemode='w',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def notes2flash(workflow_config_path, user_inputs, progress_callback=None, debug=False):
    """
    Execute the notes2flash workflow using the specified configuration and user inputs.

    Args:
        workflow_config_path (str): Path to the YAML workflow configuration file.
        user_inputs (dict): Dictionary containing user-provided inputs for the workflow.
        progress_callback (function, optional): Callback function to report progress.
        debug (bool, optional): Enable debug mode for more verbose logging.

    Returns:
        dict: The final result of the workflow execution.

    Raises:
        ValueError: If the input parameters are invalid.
        RuntimeError: If there's an error during workflow execution.
    """
    if debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")

    logger.info("Starting notes2flash execution")

    if not workflow_config_path or not isinstance(workflow_config_path, str):
        logger.error("Invalid workflow_config_path")
        raise ValueError("Invalid workflow_config_path. Must be a non-empty string.")

    if not user_inputs or not isinstance(user_inputs, dict):
        logger.error("Invalid user_inputs")
        raise ValueError("Invalid user_inputs. Must be a non-empty dictionary.")

    try:
        # Load the YAML workflow config
        logger.info("Loading workflow configuration")
        workflow_config = WorkflowEngine.load_workflow_config(workflow_config_path)

        # Run the workflow engine
        logger.info("Initializing WorkflowEngine")
        engine = WorkflowEngine(workflow_config, user_inputs, debug=debug)
        
        logger.info("Running workflow")
        success = engine.run_workflow(progress_callback)

        if success:
            logger.info("Workflow execution completed successfully")
            return engine.get_final_result()
        else:
            logger.error("Workflow execution failed without raising an exception")
            raise RuntimeError("Workflow execution failed without raising an exception.")

    except Exception as e:
        error_message = f"Error in notes2flash: {str(e)}"
        logger.exception(error_message)
        if progress_callback:
            progress_callback(error_message)
        raise RuntimeError(error_message)

    finally:
        logger.info("notes2flash execution finished")
