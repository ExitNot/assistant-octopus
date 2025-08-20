import logging
from typing import Optional

def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        level: Optional log level override
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if level:
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    return logger

def log_function_call(logger: logging.Logger, func_name: str, **kwargs):
    """
    Log function call with parameters.
    
    Args:
        logger: Logger instance
        func_name: Name of the function being called
        **kwargs: Function parameters to log
    """
    params = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.debug(f"Calling {func_name}({params})")

def log_function_result(logger: logging.Logger, func_name: str, result=None, error=None):
    """
    Log function result or error.
    
    Args:
        logger: Logger instance
        func_name: Name of the function
        result: Function result (if successful)
        error: Error that occurred (if any)
    """
    if error:
        logger.error(f"Function {func_name} failed: {error}")
    else:
        logger.debug(f"Function {func_name} completed successfully")
        if result is not None:
            logger.debug(f"Function {func_name} returned: {result}")
