import os
import sys
from loguru import logger
from app.core.config import settings


def get_logger(name: str):
    """Return a logger carrying the originating module name."""
    return logger.bind(name=name)


def setup_logging():
    """Configure logging with loguru"""
    logger.remove()  # Remove default handler
    
    # Add console handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG" if settings.DEBUG else "INFO",
        colorize=True
    )
    
    # Ensure logs directory exists before adding file handler
    os.makedirs("logs", exist_ok=True)
    
    # Add file handler
    logger.add(
        "logs/app_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="INFO"
    )
    
    return logger
