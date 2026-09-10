"""Input sanitization and output escaping utilities.

Provides helpers to prevent XSS, SQL injection (defense-in-depth),
and other injection attacks at the application layer.
"""

from __future__ import annotations

import html
import re
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Patterns that indicate potential injection attacks
_SUSPICIOUS_PATTERNS = [
    re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL),
    re.compile(r"javascript:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),
    re.compile(r"<iframe", re.IGNORECASE),
    re.compile(r"<object", re.IGNORECASE),
    re.compile(r"<embed", re.IGNORECASE),
    re.compile(r"expression\s*\(", re.IGNORECASE),
    re.compile(r"url\s*\(", re.IGNORECASE),
    re.compile(r"@import", re.IGNORECASE),
    re.compile(r"-moz-binding", re.IGNORECASE),
]

# Patterns for SQL injection detection (defense-in-depth)
_SQL_INJECTION_PATTERNS = [
    re.compile(r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|CREATE|ALTER|EXEC|EXECUTE)\b)", re.IGNORECASE),
    re.compile(r"(--|#|/\*|\*/|;)", re.IGNORECASE),
    re.compile(r"(\bOR\b\s+\d+\s*=\s*\d+)", re.IGNORECASE),
    re.compile(r"(\bAND\b\s+\d+\s*=\s*\d+)", re.IGNORECASE),
]


def sanitize_html(value: str) -> str:
    """Escape HTML special characters to prevent XSS."""
    if not isinstance(value, str):
        return value
    return html.escape(value, quote=True)


def sanitize_text(value: str, max_length: int | None = None) -> str:
    """Sanitize text input by removing suspicious patterns and normalizing whitespace."""
    if not isinstance(value, str):
        return value

    sanitized = value.strip()
    if max_length is not None and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    for pattern in _SUSPICIOUS_PATTERNS:
        if pattern.search(sanitized):
            logger.warning("Suspicious pattern detected in input: %s", pattern.pattern)
            sanitized = pattern.sub("", sanitized)

    return sanitized


def detect_sql_injection(value: str) -> bool:
    """Detect potential SQL injection patterns (defense-in-depth)."""
    if not isinstance(value, str):
        return False

    for pattern in _SQL_INJECTION_PATTERNS:
        if pattern.search(value):
            logger.warning("Potential SQL injection pattern detected: %s", value[:100])
            return True
    return False


def sanitize_search_query(value: str, max_length: int = 200) -> str:
    """Sanitize a search query string."""
    if not isinstance(value, str):
        return ""
    sanitized = re.sub(r"[^\w\s\-\.]", " ", value.strip())
    sanitized = re.sub(r"\s+", " ", sanitized)
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    return sanitized.strip()


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename by removing path traversal and special characters."""
    if not isinstance(filename, str):
        return ""
    filename = filename.strip()
    filename = re.sub(r"[^\w\-\.]", "_", filename)
    filename = re.sub(r"\.{2,}", ".", filename)
    filename = filename.lstrip(".")
    if not filename:
        filename = "unnamed"
    return filename


def validate_no_injection(value: Any, field_name: str = "input") -> None:
    """Validate that a value does not contain injection patterns.

    Raises ValueError if suspicious patterns are detected.
    """
    if not isinstance(value, str):
        return

    if detect_sql_injection(value):
        raise ValueError(
            f"Invalid input detected in {field_name}: potential SQL injection pattern"
        )

    for pattern in _SUSPICIOUS_PATTERNS:
        if pattern.search(value):
            raise ValueError(
                f"Invalid input detected in {field_name}: potential XSS pattern"
            )
