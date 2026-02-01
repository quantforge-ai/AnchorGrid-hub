"""
QuantForge AI Engine - Structured Logging

Uses loguru for structured, colorized logging.
JSON format available for production or when LOG_JSON_FORMAT=true.
"""
import sys
from loguru import logger

from anchorgrid.core.config import settings


def json_formatter(record: dict) -> str:
    """Custom JSON formatter for loguru"""
    import json
    from datetime import datetime
    
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "level": record["level"].name,
        "message": record["message"],
        "module": record["name"],
        "function": record["function"],
        "line": record["line"],
    }
    
    # Add extra fields if present
    if record.get("extra"):
        for key, value in record["extra"].items():
            if key not in ("module",):  # Skip internal keys
                log_entry[key] = value
    
    # Add exception info if present
    if record["exception"]:
        log_entry["exception"] = {
            "type": record["exception"].type.__name__ if record["exception"].type else None,
            "value": str(record["exception"].value) if record["exception"].value else None,
        }
    
    return json.dumps(log_entry) + "\n"


def setup_logging() -> None:
    """Configure structured logging"""
    # Remove default handler
    logger.remove()
    
    # Determine if we should use JSON format
    use_json = getattr(settings, "LOG_JSON_FORMAT", False) or settings.ENVIRONMENT == "production"
    
    if use_json:
        # JSON format for production or when explicitly requested
        logger.add(
            sys.stderr,
            format=json_formatter,
            level=settings.LOG_LEVEL,
            colorize=False,
        )
    else:
        # Colorized console handler for development
        logger.add(
            sys.stderr,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "<level>{message}</level>"
            ),
            level=settings.LOG_LEVEL,
            colorize=True,
        )
    
    # JSON file handler for production (always)
    if settings.ENVIRONMENT == "production":
        logger.add(
            "logs/quantforge_{time}.log",
            format=json_formatter,
            rotation="100 MB",
            retention="30 days",
            compression="gz",
            level="INFO",
        )
    
    logger.info(f"Logging configured for {settings.ENVIRONMENT} environment")


def get_logger(name: str):
    """Get a contextualized logger with module name bound"""
    return logger.bind(module=name)

