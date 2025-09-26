"""
Logging configuration for ATS system
"""
from loguru import logger
import sys
import os
from pathlib import Path

def setup_logging():
    """
    Set up logging system with console and file handlers
    """
    # Remove default handler
    logger.remove()
    
    # Ensure logs directory exists
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Add console handler with INFO level
    logger.add(
        sys.stdout, 
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # Add file handler for general logs (daily rotation, 30 days retention)
    logger.add(
        "logs/ats_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="30 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )
    
    # Add file handler for errors (weekly rotation)
    logger.add(
        "logs/errors_{time:YYYY-MM-DD}.log",
        level="ERROR",
        rotation="1 week",
        retention="4 weeks",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )
    
    logger.info("Logging system initialized")
    return logger

def get_logger(name: str = None):
    """
    Get a logger instance
    
    Args:
        name: Logger name (optional)
    
    Returns:
        Logger instance
    """
    if name:
        return logger.bind(name=name)
    return logger
