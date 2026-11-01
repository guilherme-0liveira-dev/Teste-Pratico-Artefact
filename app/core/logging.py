"""Logging configuration with sensitive data sanitization."""

import logging
import re
import sys

from app.core.config import settings

# Patterns to mask sensitive information
CPF_PATTERN = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
API_KEY_PATTERN = re.compile(r"(nvapi-[a-zA-Z0-9_-]{20,}|sk-[a-zA-Z0-9_-]{20,})")


class RedactingFormatter(logging.Formatter):
    """Custom formatter to redact sensitive customer data and API keys."""

    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        redacted = CPF_PATTERN.sub("[REDACTED_CPF]", original)
        redacted = API_KEY_PATTERN.sub("[REDACTED_KEY]", redacted)
        return redacted


def setup_logger(name: str = "emporio_ai") -> logging.Logger:
    """Setup and return a structured logger instance."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
        logger.setLevel(level)

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)

        formatter = RedactingFormatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False

    return logger


logger = setup_logger()
