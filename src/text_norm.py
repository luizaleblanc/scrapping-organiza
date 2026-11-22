"""Normalização compartilhada de títulos e desenvolvedores (entity resolution)."""
import re
import unicodedata

import pandas as pd

GENERIC_TITLE_WORDS = {"app", "the"}  # remover "finance/budget" colapsava marcas (ex.: "Minhas Finanças" -> "minhas")
DEV_SUFFIXES = re.compile(
    r"\b(inc|llc|ltd|ltda|limited|s a|sa|co|corp|corporation|gmbh|pty|technologies|"
    r"technology|tecnologia|software|solutions|solucoes|private|me|eireli|labs|apps?)\b"
)


def norm(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", text.casefold()).strip()


def brand(title) -> str:
    """Nome-base: parte antes de ':', ' - ', '–', '—', '|', '(' sem sufixos genéricos."""
    head = re.split(r"\s[-–—]\s|[:|–—(]", str(title or ""))[0]
    words = [w for w in norm(head).split() if w not in GENERIC_TITLE_WORDS]
    return " ".join(words) or norm(head)


def norm_dev(dev) -> str:
    return re.sub(r"\s+", " ", DEV_SUFFIXES.sub(" ", norm(dev))).strip()


def has_term(text: str, terms):
    """Primeiro termo da lista presente como palavra(s) inteira(s) no texto normalizado."""
    padded = f" {text} "
    for term in terms:
        if f" {norm(term)} " in padded:
            return term
    return None
