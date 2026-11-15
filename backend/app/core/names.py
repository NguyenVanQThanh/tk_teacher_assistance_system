# File Name: names.py
# Description: Shared full-name normalization and validation (NFC, letters and single spaces only).
# Created At: 2026-11-15
# Created By: AI Agent
# Updated At: 2026-11-15
# Updated By: AI Agent

import re
import unicodedata

# Unicode letters separated by single whitespace runs; digits, underscores and symbols are rejected.
_NAME_RE = re.compile(r"^[^\W\d_]+(\s+[^\W\d_]+)*$")


def normalize_full_name(value: str, min_length: int = 2) -> str:
    """Return the NFC-normalized, trimmed, space-collapsed name or raise ValueError when invalid."""
    name = unicodedata.normalize("NFC", (value or "").strip())
    if len(name) < min_length:
        raise ValueError(f"Full name must be at least {min_length} characters long.")
    if not _NAME_RE.match(name):
        raise ValueError("Full name cannot contain numbers or special characters.")
    return re.sub(r"\s+", " ", name)
