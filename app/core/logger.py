"""Global logger configuration using loguru."""
import sys
from loguru import logger as loguru_logger

from app.core.config import settings


def configure_logger():
    """Configure loguru logger with application settings."""
    # Remove default handler
    loguru_logger.remove()
    
    # Add custom handler
    loguru_logger.add(
        sys.stderr,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        level=settings.log_level,
        colorize=True,
    )
    
    return loguru_logger


# Configure logger when module is imported
logger = configure_logger()

