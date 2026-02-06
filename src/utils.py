"""Shared utilities for the bill import service."""

import logging
import datetime
from typing import List, Optional, Tuple


# ============================================================================
# Logging Configuration
# ============================================================================

class BeijingFormatter(logging.Formatter):
    """Formatter that uses Beijing timezone (UTC+8)."""

    def formatTime(self, record, datefmt=None):
        # record.created is a Unix timestamp (seconds since epoch 1970-01-01 UTC)
        # Convert to UTC datetime first, then add 8 hours for Beijing time
        dt_utc = datetime.datetime.utcfromtimestamp(record.created)
        dt_beijing = dt_utc + datetime.timedelta(hours=8)
        if datefmt:
            return dt_beijing.strftime(datefmt)
        return dt_beijing.isoformat()


def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
    """Configure logging with Beijing timezone."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    handlers = [logging.StreamHandler()]

    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=handlers
    )

    for handler in logging.getLogger().handlers:
        handler.setFormatter(BeijingFormatter('%(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))


# ============================================================================
# Encoding Detection
# ============================================================================

def read_file_lines(file_path: str, max_lines: int = 20) -> List[str]:
    """Read file lines trying multiple encodings.

    Args:
        file_path: Path to the file
        max_lines: Maximum number of lines to read

    Returns:
        List of lines, or empty list if all encodings fail
    """
    encodings = ['gbk', 'utf-8', 'gb2312', 'latin-1']

    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return [f.readline().strip() for _ in range(max_lines)]
        except UnicodeDecodeError:
            continue

    return []


def find_header_and_encoding(file_path: str, keywords: List[str], encodings: Optional[List[str]] = None) -> Tuple[int, str]:
    """Find the header line in a file.

    Args:
        file_path: Path to the file
        keywords: List of keywords to search for
        encodings: List of encodings to try (default: ['gbk', 'utf-8', 'gb2312'])

    Returns:
        Tuple of (header_line_index, encoding) or (-1, '') if not found
    """
    if encodings is None:
        encodings = ['gbk', 'utf-8', 'gb2312']

    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                lines = f.readlines()

            for i, line in enumerate(lines):
                if any(keyword in line for keyword in keywords):
                    return i, encoding
        except (UnicodeDecodeError, Exception):
            continue

    return -1, ''
