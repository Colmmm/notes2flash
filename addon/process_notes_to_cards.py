"""Main module for processing notes into flashcards."""
import logging
import json
from typing import List, Dict, Any
from .processing_utils import (
    split_content_into_chunks,
    format_prompt_safely,
    get_content_key_from_previous_step,
    get_api_key_from_config,
    extract_json_from_response,
    validate_step_config,
    prepare_step_input,
    validate_output,
    call_openrouter_api
)

logger = logging.getLogger("notes2flash")

def process_chunk_through_steps(chunk: str, stage_config: List[Dict[str, Any]], stage_data: Dict[str, Any], 
                              workflow_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single chunk through all workflow steps.
    
    Args:
        chunk: The content chunk to process
        stage_config: List of processing step configurations
        stage_data: Current stage data
        workflow_config: Complete workflow configuration
        
    Returns:
        Dictionary containing the results of processing the chunk through all steps
    """
    chunk_state = stage_data.copy()
    chunk_output = {}
    
    for step_index, step_config in enumerate(stage_config):
        try:
            # Get content key from previous step
            content_key, source = get_content_key_from_previous_step(step_index, stage_config, workflow_config)
            logger.debug(f"Using content key '{content_key}' from {source}")
            
            # Validate and extract step configuration
            validated_config = validate_step_config(step_config, step_index, stage_config)
            
            # Prepare input data for this step
            step_input = prepare_step_input(
                validated_config['input_keys'], 
                chunk_state,
                content_key,
                chunk if step_index == 0 else chunk_state[content_key]
            )
            
            # Process the chunk
            result = call_openrouter_api(validated_config['prompt'], validated_config['model'], step_input)
            
            # For intermediate steps, we just need the raw output as a string
            is_final_step = step_index == len(stage_config) - 1
            
            if is_final_step:
                # Only validate structure for the final step
                if not result or not isinstance(result, list):
                    logger.error("Failed to parse JSON from final step response")
                    return {}
                    
                # Validate output fields only for final step
                if validated_config['output_fields']:
                    validate_output(result, validated_config['output_fields'])
                    
                # Update state with parsed JSON result
                step_result = {validated_config['output_name']: result}
            else:
                # For intermediate steps, store the raw JSON string
                step_result = {validated_config['output_name']: json.dumps(result) if result else ""}
            
            # Update states
            chunk_state.update(step_result)
            chunk_output.update(step_result)
            
        except Exception as e:
            logger.error(f"Error processing step {step_config.get('step', 'unnamed')}: {str(e)}")
            raise
            
    return chunk_output

def process_notes_to_cards(stage_data: Dict[str, Any], stage_config: List[Dict[str, Any]], workflow_config: Dict[str, Any]) -> Dict[str, Any]:
    """Process notes to cards using the provided configuration, processing each chunk through all steps."""
    logger.info("Starting process_notes_to_cards")
    
    if not isinstance(stage_config, list) or len(stage_config) == 0:
        raise ValueError("Invalid stage_config. Expected a non-empty list.")

    # Get initial content key and chunk size from first step
    content_key, _ = get_content_key_from_previous_step(0, stage_config, workflow_config)
    chunk_size = int(stage_config[0].get('chunk_size', 4000))
    
    # Split the initial content into chunks
    initial_content = stage_data.get(content_key)
    if not initial_content:
        raise ValueError(f"Initial content key '{content_key}' not found in stage data")
        
    chunks = split_content_into_chunks(initial_content, chunk_size)
    if len(chunks) > 1:
        logger.info(f"Processing content in {len(chunks)} chunks")

    # Process each chunk through all steps
    all_results = {}
    for i, chunk in enumerate(chunks, 1):
        if len(chunks) > 1:
            logger.info(f"Processing chunk {i} of {len(chunks)}")
            
        try:
            # Process this chunk through all steps
            chunk_results = process_chunk_through_steps(chunk, stage_config, stage_data, workflow_config)
            
            # Merge chunk results with all results
            for key, value in chunk_results.items():
                if key not in all_results:
                    # Initialize based on whether this is a list (final step) or string (intermediate step)
                    all_results[key] = [] if isinstance(value, list) else ""
                
                if isinstance(value, list):
                    # For final step results (lists), extend the list
                    all_results[key].extend(value)
                else:
                    # For intermediate step results (strings), concatenate
                    all_results[key] += value
                
        except Exception as e:
            logger.error(f"Error processing chunk {i}: {str(e)}")
            raise

    logger.info("Completed process_notes_to_cards")
    logger.debug(f"Final output: {all_results}")
    return all_results
