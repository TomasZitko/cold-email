"""
Logging utilities for the cold email system.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


class SystemLogger:
    """Centralized logging system."""

    _instances = {}

    @classmethod
    def get_logger(cls, name: str, config: Optional[dict] = None) -> logging.Logger:
        """Get or create a logger instance."""
        if name in cls._instances:
            return cls._instances[name]

        logger = logging.getLogger(name)

        # Default config
        if config is None:
            config = {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'files': {
                    'main': 'logs/system.log',
                    'errors': 'logs/errors.log'
                },
                'rotation': {
                    'max_bytes': 10485760,  # 10MB
                    'backup_count': 5
                }
            }

        # Set level
        log_level = getattr(logging, config.get('level', 'INFO').upper())
        logger.setLevel(log_level)

        # Formatter
        formatter = logging.Formatter(
            config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handlers
        files_config = config.get('files', {})
        rotation_config = config.get('rotation', {})

        # Main log file
        if 'main' in files_config:
            main_file = Path(files_config['main'])
            main_file.parent.mkdir(parents=True, exist_ok=True)

            main_handler = RotatingFileHandler(
                main_file,
                maxBytes=rotation_config.get('max_bytes', 10485760),
                backupCount=rotation_config.get('backup_count', 5)
            )
            main_handler.setLevel(log_level)
            main_handler.setFormatter(formatter)
            logger.addHandler(main_handler)

        # Error log file
        if 'errors' in files_config:
            error_file = Path(files_config['errors'])
            error_file.parent.mkdir(parents=True, exist_ok=True)

            error_handler = RotatingFileHandler(
                error_file,
                maxBytes=rotation_config.get('max_bytes', 10485760),
                backupCount=rotation_config.get('backup_count', 5)
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)
            logger.addHandler(error_handler)

        cls._instances[name] = logger
        return logger


def log_function_call(func):
    """Decorator to log function calls."""
    def wrapper(*args, **kwargs):
        logger = SystemLogger.get_logger(func.__module__)
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed: {str(e)}", exc_info=True)
            raise
    return wrapper
