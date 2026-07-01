"""
Logging setup utility for candidate data transformer.
Includes custom color formatting for terminal display.
"""

import logging
import sys
from typing import Optional


# ANSI escape sequences for formatting
COLOR_RESET = "\033[0m"
COLOR_DEBUG = "\033[36m"    # Cyan
COLOR_INFO = "\033[32m"     # Green
COLOR_WARNING = "\033[33m"  # Yellow
COLOR_ERROR = "\033[31m"    # Red
COLOR_CRITICAL = "\033[1;31m" # Bold Red
COLOR_PREFIX = "\033[90m"   # Dark Gray


class TerminalFormatter(logging.Formatter):
    """Custom color-coded formatting for pipeline logs in terminal."""

    def format(self, record: logging.LogRecord) -> str:
        # Determine color by level
        if record.levelno == logging.DEBUG:
            color = COLOR_DEBUG
        elif record.levelno == logging.INFO:
            color = COLOR_INFO
        elif record.levelno == logging.WARNING:
            color = COLOR_WARNING
        elif record.levelno == logging.ERROR:
            color = COLOR_ERROR
        elif record.levelno == logging.CRITICAL:
            color = COLOR_CRITICAL
        else:
            color = COLOR_RESET

        # Custom format structure
        time_str = self.formatTime(record, "%H:%M:%S")
        prefix = f"{COLOR_PREFIX}[{time_str}] [{record.name}]{COLOR_RESET}"
        level_lbl = f"{color}{record.levelname:<7}{COLOR_RESET}"
        message = record.getMessage()

        return f"{prefix} {level_lbl} | {message}"


def get_logger(name: str) -> logging.Logger:
    """Gets or configures a logger for the given module name."""
    logger = logging.getLogger(name)
    return logger


def configure_logging(level: int = logging.INFO) -> None:
    """Configures global logging with our custom formatter."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clean existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(TerminalFormatter())
    root_logger.addHandler(console_handler)
