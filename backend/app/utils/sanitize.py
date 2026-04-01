"""
VyapaarBandhu -- Input Sanitization Utilities
Strips HTML, null bytes, and enforces length limits on free-text input.
"""

import re

# Regex to match HTML tags (including self-closing and with attributes)
_HTML_TAG_RE = re.compile(r"<[^>]+>")


def sanitize_string(value: str, max_length: int) -> str:
    """
    Sanitize a free-text string input.

    Steps:
      1. Strip leading/trailing whitespace
      2. Remove null bytes
      3. Strip HTML tags via regex
      4. Truncate to max_length
      5. Raise ValueError if the result is empty

    Args:
        value: The raw input string.
        max_length: Maximum allowed length after sanitization.

    Returns:
        The sanitized string.

    Raises:
        ValueError: If the string is empty after sanitization.
    """
    if not isinstance(value, str):
        raise ValueError("Input must be a string")

    # Strip whitespace
    result = value.strip()

    # Remove null bytes
    result = result.replace("\x00", "")

    # Remove HTML tags
    result = _HTML_TAG_RE.sub("", result)

    # Strip again after tag removal (tags may leave leading/trailing space)
    result = result.strip()

    # Truncate to max length
    result = result[:max_length]

    # Final strip in case truncation left trailing whitespace
    result = result.strip()

    if not result:
        raise ValueError("Input is empty after sanitization")

    return result
