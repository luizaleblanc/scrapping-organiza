"""Etapa 1 — Busca na Google Play (Brasil; ou MARKET=us|es|mx) somente as strings aprovadas (top 30 cada).

Saída: data/brasil/google_play_store/busca_e_triagem/search_hits.csv (1 linha por ocorrência string x app,
com metadados e descrição oficial para a triagem).
"""
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from google_play_scraper import app as play_app, search

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
from rules import update_metrics, write_csv  # noqa: E402


MONTHS_PT = {"jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6,
             "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11, "dez": 12}


def page_updated(app_id):
    """Fallback: lê 'Atualizado em' da página pública do app quando a biblioteca
    google-play-scraper devolve updated=None. Retorna Unix seconds ou None."""
    try:
        html = requests.get("https://play.google.com/store/apps/details",
                            params={"id": app_id, "hl": "pt_BR", "gl": "BR"}, timeout=30).text  # regex em pt; data é igual em todo país
    except requests.RequestException:
        return None
    m = re.search(r"Atualizado em</div><div[^>]*>(\d{1,2}) de ([a-z]{3})\.? de (\d{4})<", html)
    if not m or m.group(2) not in MONTHS_PT:
        return None
    dt = datetime(int(m.group(3)), MONTHS_PT[m.group(2)], int(m.group(1)), tzinfo=timezone.utc)
    return int(dt.timestamp())


def fill_missing_dates(hits):
    """Completa 'updated' vazio pela página do app e registra a origem do dado."""
    hits["updated_source"] = hits.get("updated_source", pd.Series(index=hits.index, dtype=object))
    hits.loc[hits.updated.notna() & hits.updated_source.isna(), "updated_source"] = "google_play_scraper"
    for app_id in hits.loc[hits.updated.isna(), "appId"].unique():
        ts = page_updated(app_id)
        mask = hits.appId.eq(app_id)
        hits.loc[mask, "updated"] = ts
        hits.loc[mask, "updated_source"] = "play_store_page_atualizado_em" if ts else "unavailable"
        print(f"  data via página: {app_id} -> {ts}")
        time.sleep(C.REQUEST_DELAY_SECONDS)
    return hits


def page_search(term):
    """Fallback: ids na ordem em que aparecem na página pública de busca da Play Store."""
    html = requests.get("https://play.google.com/store/search",
                        params={"q": term, "c": "apps", "hl": C.HL, "gl": C.GL}, timeout=30).text
    ids = dict.fromkeys(re.findall(r"/store/apps/details\?id=([\w.]+)", html))
    return [{"appId": i} for i in ids]


def retry(fn, *args, **kwargs):
    for attempt in range(4):
        try:
            return fn(*args, **kwargs)
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 ** (attempt + 1))


def main():
    collected_at = datetime.now(timezone.utc).isoformat()
    details_cache, rows = {}, []
    for term_id, term in C.SEARCH_STRINGS.items():
        try:
            results = retry(search, term, lang=C.LANG, country=C.COUNTRY, n_hits=C.RESULTS_PER_TERM)
        except TypeError:  # bug da biblioteca ao ler o "resultado em destaque" de algumas buscas
            results = page_search(term)
            print(f"  {term!r}: busca pela página pública da Play Store (fallback)")
        results = [r for r in results if r.get("appId")][: C.RESULTS_PER_TERM]
        print(f"{term_id} {term!r}: {len(results)} resultados")
        for rank, res in enumerate(results, 1):
            app_id = res["appId"]
            if app_id not in details_cache:
                try:
                    details_cache[app_id] = retry(play_app, app_id, lang=C.LANG, country=C.COUNTRY)
                except Exception as exc:  # metadado indisponível: registra o que a busca trouxe
                    print(f"  metadados indisponíveis para {app_id}: {exc}")
                    details_cache[app_id] = res
                time.sleep(C.REQUEST_DELAY_SECONDS)
            d = details_cache[app_id]
            rows.append({
                "appId": app_id, "title": d.get("title") or res.get("title"),
                "developer": d.get("developer") or res.get("developer"),
                "genre": d.get("genre"), "installs": d.get("installs"),
                "ratings": d.get("ratings"), "reviews": d.get("reviews"), "score": d.get("score"),
                "updated": d.get("updated"), "url": d.get("url") or f"https://play.google.com/store/apps/details?id={app_id}",
                "description": d.get("description") or res.get("summary") or "",
                "term_id": term_id, "term": term, "country": C.COUNTRY, "rank": rank,
                "collected_at": collected_at,
            })
    hits = fill_missing_dates(pd.DataFrame(rows))
    write_csv(hits, C.PATHS["gp_hits"])
    update_metrics("01_google_play_search", {
        "strings": C.SEARCH_STRINGS, "country": C.COUNTRY, "collected_at": collected_at,
        "hits": int(len(hits)), "unique_apps": int(hits.appId.nunique()),
    })
    print(f"{len(hits)} ocorrências, {hits.appId.nunique()} apps únicos -> {C.PATHS['gp_hits']}")


if __name__ == "__main__":
    if "--fill-missing-dates" in sys.argv:  # completa datas sem refazer a busca
        h = fill_missing_dates(pd.read_csv(C.PATHS["gp_hits"], encoding="utf-8-sig"))
        write_csv(h, C.PATHS["gp_hits"])
    else:
        main()
