"""Etapa 2 — Busca na App Store (Brasil; ou MARKET=us|es|mx) somente as strings aprovadas (top 30 cada).

Usa só a iTunes Search API oficial. A Apple serve apenas para busca/triagem
(critério 4); nenhum review da App Store é coletado.
Saída: data/brasil/app_store/busca_e_triagem/search_hits.csv
"""
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
from rules import update_metrics, write_csv  # noqa: E402

API = "https://itunes.apple.com/search"
FIELDS = ["trackId", "bundleId", "trackName", "artistName", "primaryGenreName",
          "averageUserRating", "userRatingCount", "currentVersionReleaseDate",
          "trackViewUrl", "description"]


def search(term):
    last = None
    for attempt in range(5):
        try:
            r = requests.get(API, params={"term": term, "entity": "software", "country": C.COUNTRY,
                                          "limit": C.RESULTS_PER_TERM}, timeout=25)
            r.raise_for_status()
            return r.json().get("results", [])
        except (requests.RequestException, ValueError) as exc:
            last = exc
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"Falha na busca {term!r}: {last}")


def main():
    collected_at = datetime.now(timezone.utc).isoformat()
    rows = []
    for term_id, term in C.SEARCH_STRINGS.items():
        results = search(term)
        print(f"{term_id} {term!r}: {len(results)} resultados")
        for rank, res in enumerate(results, 1):
            rows.append({**{f: res.get(f) for f in FIELDS}, "term_id": term_id, "term": term,
                         "country": C.COUNTRY, "rank": rank, "collected_at": collected_at})
        time.sleep(C.APP_STORE_DELAY_SECONDS)
    hits = pd.DataFrame(rows)
    write_csv(hits, C.PATHS["as_hits"])
    update_metrics("02_app_store_search", {
        "strings": C.SEARCH_STRINGS, "country": C.COUNTRY, "collected_at": collected_at,
        "hits": int(len(hits)), "unique_apps": int(hits.trackId.nunique()),
    })
    print(f"{len(hits)} ocorrências, {hits.trackId.nunique()} apps únicos -> {C.PATHS['as_hits']}")


if __name__ == "__main__":
    main()
