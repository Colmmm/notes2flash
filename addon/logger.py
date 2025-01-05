import logging
import os

def setup_logger(debug=False):
    """
    Set up a custom logger for notes2flash.
    
    Args:
        debug (bool): Whether to enable debug logging level
        
    Returns:
        logging.Logger: Configured logger instance
    """
    addon_folder = os.path.dirname(__file__)
    log_file = os.path.join(addon_folder, "notes2flash.log")
    
    # Create logger
    logger = logging.getLogger("notes2flash")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    
    # Create file handler
    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Remove existing handlers to prevent duplicates
    logger.handlers.clear()
    
    # Add handler to logger
    logger.addHandler(file_handler)
    
    return logger

# Initialize logger with default settings
logger = setup_logger()

def get_logger():
    """
    Get the notes2flash logger instance.
    
    Returns:
        logging.Logger: The configured logger instance
    """
    return logger

def reinitialize_logger(debug=False):
    """
    Reinitialize the logger with new settings.
    
    Args:
        debug (bool): Whether to enable debug logging level
        
    Returns:
        logging.Logger: Reinitialized logger instance
    """
    global logger
    logger = setup_logger(debug=debug)
    if debug:
        logger.debug("Debug mode enabled")
    return logger
