"""Exact quote checking: is a quote really in the source document?

This is plain string matching, no model involved. Only whitespace and typographic
characters (curly quotes, different dashes, non-breaking spaces) are ignored, so a
quote that was reworded, shortened with "...", or invented is NOT accepted.
"""

import re
import unicodedata

_REPLACEMENTS = {
    "‘": "'", "’": "'", "‚": "'", "‛": "'",
    "“": '"', "”": '"', "„": '"',
    "‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-", "−": "-",
    "­": "",  # soft hyphen
}


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    for old, new in _REPLACEMENTS.items():
        text = text.replace(old, new)
    return re.sub(r"\s+", " ", text).strip()


def quote_in_source(quote: str, source: str) -> bool:
    """True if the (non-empty) quote appears word for word in the source."""
    q = normalize(quote)
    if not q:
        return False
    return q in normalize(source)


def check_quotes(quotes: list[str], source: str) -> list[bool]:
    return [quote_in_source(q, source) for q in quotes]
