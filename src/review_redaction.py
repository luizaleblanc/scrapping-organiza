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
    # Nome que o próprio avaliador escreve ("Meu nome é Fulano de Tal", "Att. Fulano").
    # Troca só o nome (até 5 palavras com maiúscula, aceitando de/da/do/dos/das/del/y/e).
    "name": re.compile(
        r"(\b(?:[Mm]eu nome (?:é|e)|[Mm]e chamo|[Mm]y name is|[Mm]e llamo|[Mm]i nombre es|"
        r"[Aa]tt\.?|[Aa]ss\.?|[Aa]tenciosamente,?|[Aa]tentamente,?|[Ss]incerely,?|[Rr]egards,?) )"
        r"[A-ZÁÉÍÓÚÂÊÔÃÕÇÑ][a-záéíóúâêôãõçñ'-]+"  # minúsculas depois da inicial: siglas (CPF) não contam
        r"(?: (?:(?:de|da|do|dos|das|del|y|e) )?[A-ZÁÉÍÓÚÂÊÔÃÕÇÑ][a-záéíóúâêôãõçñ'-]+){0,4}"
    ),
}
REDACTION_LABELS = {
    "email": "[EMAIL]",
    "url": "[URL]",
    "cpf": "[CPF]",
    "phone": "[PHONE]",
    "handle": "[HANDLE]",
    "name": r"\g<1>[NOME]",  # mantém "Meu nome é", troca só o nome
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


# ---------------------------------------------------------------------------
# Nomes de pessoas em qualquer lugar do texto (pt, en, es): modelo de NER multilíngue.
# Regras não pegam nome solto ("o atendente Carlos me ignorou"). O modelo às vezes marca
# nome de app como pessoa; nesse caso censura a mais, o que não expõe ninguém.
# ---------------------------------------------------------------------------
NER_MODEL = "Davlan/bert-base-multilingual-cased-ner-hrl"
NER_MIN_SCORE = 0.6
_ner = None


def redact_person_names(texts, counters=None, batch_size=32):
    """Troca por [NOME] toda entidade PER encontrada. Recebe e devolve uma lista de textos."""
    global _ner
    if counters is None:
        counters = {}
    if _ner is None:
        from transformers import pipeline
        _ner = pipeline("ner", model=NER_MODEL, aggregation_strategy="simple")
    texts = ["" if pd.isna(t) else str(t) for t in texts]
    # Pedaços de até ~800 caracteres (cortados em espaço) para caber no limite do modelo
    # e nenhum trecho de review longa ficar sem verificação.
    pieces = []  # (índice do texto, deslocamento, trecho)
    for i, t in enumerate(texts):
        pos = 0
        while pos < len(t):
            end = len(t) if len(t) - pos <= 800 else (t.rfind(" ", pos, pos + 800) if t.rfind(" ", pos, pos + 800) > pos else pos + 800)
            if t[pos:end].strip():
                pieces.append((i, pos, t[pos:end]))
            pos = end
    results = _ner([p[2] for p in pieces], batch_size=batch_size) if pieces else []
    spans = {}
    for (i, off, _), ents in zip(pieces, results):
        spans.setdefault(i, []).extend((off + e["start"], off + e["end"]) for e in ents
                                       if e["entity_group"] == "PER" and e["score"] >= NER_MIN_SCORE)
    out = list(texts)
    for i, sp in spans.items():
        for start, end in sorted(sp, reverse=True):
            out[i] = out[i][:start] + "[NOME]" + out[i][end:]
        counters["person_name"] = counters.get("person_name", 0) + len(sp)
    return out
