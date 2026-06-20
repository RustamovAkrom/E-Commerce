"""Core utility functions."""

from __future__ import annotations

import re
import unicodedata

_CYRILLIC_TRANSLITERATION = str.maketrans(
    {
        "а": "a",
        "б": "b",
        "в": "v",
        "г": "g",
        "д": "d",
        "е": "e",
        "ё": "e",
        "ж": "zh",
        "з": "z",
        "и": "i",
        "й": "y",
        "к": "k",
        "л": "l",
        "м": "m",
        "н": "n",
        "о": "o",
        "п": "p",
        "р": "r",
        "с": "s",
        "т": "t",
        "у": "u",
        "ф": "f",
        "х": "h",
        "ц": "ts",
        "ч": "ch",
        "ш": "sh",
        "щ": "sch",
        "ъ": "",
        "ы": "y",
        "ь": "",
        "э": "e",
        "ю": "yu",
        "я": "ya",
    }
)


def generate_slug(
    name: str, existing_slugs: set[str] | None = None, max_length: int = 255
) -> str:
    """Generate a URL-friendly slug from a name string."""
    transliterated = name.lower().translate(_CYRILLIC_TRANSLITERATION)
    normalized = unicodedata.normalize("NFKD", transliterated)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")
    slug = re.sub(r"-+", "-", slug) or "untitled"
    slug = slug[:max_length].strip("-") or "untitled"

    if existing_slugs is None:
        existing_slugs = set()

    base_slug = slug
    counter = 1
    while slug in existing_slugs:
        suffix = f"-{counter}"
        trimmed_base = base_slug[: max_length - len(suffix)].strip("-")
        slug = f"{trimmed_base or 'untitled'}{suffix}"
        counter += 1

    return slug


def sanitize_password(value: str) -> str:
    """Sanitize a password string for safe storage/display.

    Removes control characters and normalizes whitespace.
    """
    if not value:
        return value
    sanitized = "".join(c for c in value if c.isprintable() or c in ("\n", "\t"))
    return sanitized.strip()


def format_currency(amount: float | int, currency: str = "UZS") -> str:
    """Format a numeric amount with currency symbol/code."""
    if currency == "UZS":
        return f"{amount:,.0f} {currency}"
    return f"{amount:,.2f} {currency}"
