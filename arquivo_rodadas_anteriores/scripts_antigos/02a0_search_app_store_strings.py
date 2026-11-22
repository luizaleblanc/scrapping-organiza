"""Busca na App Store Brasil SOMENTE as strings aprovadas (config.APP_STORE_APPROVED_STRINGS).

Usa apenas a iTunes Search API oficial (top 30 por termo). Não coleta reviews da Apple.
Saídas (novas, não sobrescrevem dados anteriores):
  data/raw/app_store/approved_strings/search_hits.csv   (1 linha por ocorrência termo x app)
  data/raw/app_store/approved_strings/apps_raw.csv (1 linha por app, termos agregados)
  data/raw/app_store/approved_strings/search_hits_out_of_scope.csv (descartes com motivo)
"""
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
from text_norm import has_term, norm  # noqa: E402

API = "https://itunes.apple.com/search"
FIELDS = ["trackId", "bundleId", "trackName", "artistName", "primaryGenreName",
          "averageUserRating", "userRatingCount", "version", "currentVersionReleaseDate",
          "releaseDate", "price", "currency", "trackViewUrl"]


def search(term, country):
    last = None
    for attempt in range(5):
        try:
            r = requests.get(API, params={"term": term, "entity": "software", "country": country,
                                          "limit": C.APP_STORE_RESULTS_PER_TERM}, timeout=25)
            r.raise_for_status()
            return r.json().get("results", [])
        except (requests.RequestException, ValueError) as exc:
            last = exc
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"Falha na busca {term!r}: {last}")


def main():
    collected = datetime.now(timezone.utc).isoformat()
    rows = []
    for term_id, term in C.APP_STORE_APPROVED_STRINGS.items():
        results = search(term, C.APP_STORE_COUNTRY)
        print(f"{term_id} {term!r}: {len(results)} resultados")
        for rank, res in enumerate(results, 1):
            rows.append({**{f: res.get(f) for f in FIELDS}, "term_id": term_id, "term": term,
                         "scope": "pt", "lang": "pt", "country": C.APP_STORE_COUNTRY,
                         "rank": rank, "collected_at": collected})
        time.sleep(3.2)
    all_hits = pd.DataFrame(rows)
    C.APP_STORE_RAW_INPUT.parent.mkdir(parents=True, exist_ok=True)
    split_hits(all_hits)


def out_of_scope_reason(row):
    if norm(row.primaryGenreName) not in C.FINANCE_CATEGORIES:
        return f"categoria_{norm(row.primaryGenreName).replace(' ', '_')}_fora_de_finance"
    text = f"{norm(row.trackName)} {norm(row.artistName)}"
    hit = has_term(text, C.EXCLUDE_BANKS)
    if hit:
        return f"banco_ou_maquininha:{hit}"
    hit = has_term(text, C.EXCLUDE_WALLETS_PAYMENTS)
    if hit:
        return f"carteira_ou_pagamento:{hit}"
    return ""


def split_hits(all_hits):
    """Mantém só Finance sem bancos/maquininhas/pagamentos; o resto vai para auditoria."""
    all_hits = all_hits.drop(columns=["out_of_scope_reason"], errors="ignore")
    reason = all_hits.apply(out_of_scope_reason, axis=1)
    out = all_hits[reason.ne("")].assign(out_of_scope_reason=reason[reason.ne("")])
    out.to_csv(C.APP_STORE_HITS_OUT_OF_SCOPE, index=False, encoding="utf-8-sig")
    hits = all_hits[reason.eq("")]
    hits.to_csv(C.APP_STORE_HITS_INPUT, index=False, encoding="utf-8-sig")
    print(f"Descartados na busca: {len(out)} ocorrências "
          f"({out.drop_duplicates('trackId').out_of_scope_reason.str.split(':').str[0].value_counts().to_dict()})")
    cand = (hits.sort_values("rank")
            .groupby("trackId", as_index=False)
            .agg({**{f: "first" for f in FIELDS if f != "trackId"},
                  "term": lambda s: ";".join(dict.fromkeys(s)),
                  "scope": "first", "country": "first", "rank": "min", "collected_at": "first"})
            .rename(columns={"term": "matched_terms", "scope": "matched_scopes",
                             "country": "matched_regions", "rank": "best_rank"}))
    cand.to_csv(C.APP_STORE_RAW_INPUT, index=False, encoding="utf-8-sig")
    print(f"{len(hits)} ocorrências; {len(cand)} apps únicos -> {C.APP_STORE_RAW_INPUT}")


if __name__ == "__main__":
    if "--resplit" in sys.argv:  # refaz o filtro sem nova consulta à API
        parts = [pd.read_csv(p, encoding="utf-8-sig") for p in
                 (C.APP_STORE_HITS_ALL, C.APP_STORE_HITS_INPUT, C.APP_STORE_HITS_OUT_OF_SCOPE) if p.exists()]
        split_hits(pd.concat(parts).drop_duplicates(["trackId", "term_id"]))
    else:
        main()
