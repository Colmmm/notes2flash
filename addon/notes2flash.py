from .workflow_engine import WorkflowEngine

def notes2flash(workflow_config_path, user_inputs, progress_callback=None):
    """
    Execute the notes2flash workflow using the specified configuration and user inputs.

    Args:
        workflow_config_path (str): Path to the YAML workflow configuration file.
        user_inputs (dict): Dictionary containing user-provided inputs for the workflow.
        progress_callback (function, optional): Callback function to report progress.

    Returns:
        dict: The final result of the workflow execution.

    Raises:
        ValueError: If the input parameters are invalid.
        RuntimeError: If there's an error during workflow execution.
    """
    if not workflow_config_path or not isinstance(workflow_config_path, str):
        raise ValueError("Invalid workflow_config_path. Must be a non-empty string.")

    if not user_inputs or not isinstance(user_inputs, dict):
        raise ValueError("Invalid user_inputs. Must be a non-empty dictionary.")

    try:
        # Load the YAML workflow config
        workflow_config = WorkflowEngine.load_workflow_config(workflow_config_path)

        # Run the workflow engine
        engine = WorkflowEngine(workflow_config, user_inputs)
        success = engine.run_workflow(progress_callback)

        if success:
            return engine.get_final_result()
        else:
            raise RuntimeError("Workflow execution failed without raising an exception.")

    except Exception as e:
        error_message = f"Error in notes2flash: {str(e)}"
        if progress_callback:
            progress_callback(error_message)
        raise RuntimeError(error_message)

