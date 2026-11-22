"""Conservative, deterministic redaction for public review text before storage/sharing."""
import re

import pandas as pd

REDACTION_PATTERNS = {
    "email": re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"),
    "url": re.compile(r"(?i)\b(?:https?://|www\.)\S+"),
    "cpf": re.compile(r"(?<!\d)(?:\d{3}\.?){2}\d{3}-?\d{2}(?!\d)"),
    "phone": re.compile(
        r"(?<!\w)(?:\+?\d{1,3}[\s.-]?)?(?:\(\d{2,4}\)|\d{2,4})"
        r"[\s.-]\d{3,5}[\s.-]\d{4}(?!\w)"
    ),
    "handle": re.compile(r"(?<![\w.+-])@[A-Za-z0-9_][A-Za-z0-9_.-]{1,30}"),
}
REDACTION_LABELS = {
    "email": "[EMAIL]",
    "url": "[URL]",
    "cpf": "[CPF]",
    "phone": "[PHONE]",
    "handle": "[HANDLE]",
}
POSSIBLE_NUMBER = re.compile(r"(?<!\d)(?:\d[ .-]{0,2}){7,10}\d(?!\d)")
DATE_SHAPE = re.compile(r"^(?:\d{4}[.-]\d{2}[.-]\d{2}|\d{2}[.-]\d{2}[.-]\d{4})$")
MONEY_MARKER = re.compile(r"(?i)(?:R\$|[$€£])")


def _is_ambiguous_phone_or_number(candidate, text, start, end):
    digit_count = sum(character.isdigit() for character in candidate)
    surrounding = text[max(0, start - 6):min(len(text), end + 6)]
    return (
        8 <= digit_count <= 11
        and not DATE_SHAPE.fullmatch(candidate)
        and not MONEY_MARKER.search(surrounding)
    )


def redact_text(value, counters=None):
    """Redact direct identifiers and ambiguous phone-like number strings."""
    text = "" if pd.isna(value) else str(value)
    if counters is None:
        counters = {}
    for kind, pattern in REDACTION_PATTERNS.items():
        text, count = pattern.subn(REDACTION_LABELS[kind], text)
        counters[kind] = counters.get(kind, 0) + count

    def replace_possible_number(match):
        if _is_ambiguous_phone_or_number(match.group(0), text, match.start(), match.end()):
            kind = "possible_phone_or_number"
            counters[kind] = counters.get(kind, 0) + 1
            return "[POSSIBLE_PHONE_OR_NUMBER]"
        return match.group(0)

    return POSSIBLE_NUMBER.sub(replace_possible_number, text)


def possible_number_counts(series):
    """Count ambiguous phone-like patterns without returning their text."""
    rows = matches = 0
    for value in series.fillna("").astype(str):
        row_matches = 0
        for match in POSSIBLE_NUMBER.finditer(value):
            if _is_ambiguous_phone_or_number(
                match.group(0), value, match.start(), match.end()
            ):
                row_matches += 1
        matches += row_matches
        rows += int(row_matches > 0)
    return {"matches": matches, "rows": rows}
