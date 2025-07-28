"""
Logging configuration for the AI Agent Platform.
Provides structured logging with Azure Application Insights integration.
"""

import logging
import sys
from typing import Optional
from pythonjsonlogger import jsonlogger

from src.core.config import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for structured logging."""
    
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        
        # Add custom fields
        log_record['app_name'] = settings.app_name
        log_record['app_version'] = settings.app_version
        log_record['environment'] = settings.environment
        
        # Add level name
        log_record['level'] = record.levelname
        
        # Add module and function info
        log_record['module'] = record.module
        log_record['function'] = record.funcName


def setup_logging(
    level: Optional[str] = None,
    json_format: bool = True
) -> logging.Logger:
    """
    Set up application logging configuration.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Whether to use JSON formatting
        
    Returns:
        Configured logger instance
    """
    log_level = level or settings.log_level
    
    # Create logger
    logger = logging.getLogger(settings.app_name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    if json_format:
        # JSON formatter for production
        formatter = CustomJsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s'
        )
    else:
        # Simple formatter for development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Prevent duplicate logs
    logger.propagate = False
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module."""
    return logging.getLogger(f"{settings.app_name}.{name}")


# Initialize default logger
default_logger = setup_logging(
    json_format=(settings.environment == "production")
)
