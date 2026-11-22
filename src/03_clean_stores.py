"""Etapa 3 — Higieniza as duas lojas com as MESMAS regras e deduplica dentro de cada loja.

Critérios: 2 (Finance), 1/5 (sem bancos, maquininhas, pagamentos, trading/cripto/
investimento, B2B/crédito; checagem também na descrição oficial), 3 (avaliações > 0)
e 6 (atualizado nos últimos 12 meses).
Saídas por loja: apps_eligible.csv e apps_excluded_audit.csv (com exclusion_reason).
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
from rules import REASONS, classify, update_metrics, write_csv  # noqa: E402

STORES = {
    "google_play_store": dict(
        hits="gp_hits", eligible="gp_eligible", excluded="gp_excluded", key="appId",
        title="title", developer="developer", category="genre", ratings="ratings",
        updated=lambda s: pd.to_datetime(pd.to_numeric(s, errors="coerce"), unit="s", utc=True),
        keep=["appId", "title", "developer", "genre", "installs", "ratings", "reviews", "score",
              "updated_utc", "url"],
    ),
    "app_store": dict(
        hits="as_hits", eligible="as_eligible", excluded="as_excluded", key="trackId",
        title="trackName", developer="artistName", category="primaryGenreName",
        ratings="userRatingCount",
        updated=lambda s: pd.to_datetime(s, utc=True, errors="coerce"),
        keep=["trackId", "bundleId", "trackName", "artistName", "primaryGenreName",
              "averageUserRating", "userRatingCount", "updated_utc", "trackViewUrl"],
    ),
}


def clean_store(name, cfg):
    hits = pd.read_csv(C.PATHS[cfg["hits"]], encoding="utf-8-sig")
    key = cfg["key"]
    terms = hits.groupby(key).agg(
        search_terms=("term", lambda s: ";".join(dict.fromkeys(s))),
        term_ids=("term_id", lambda s: ";".join(dict.fromkeys(s))),
        best_rank=("rank", "min"),
    )
    apps = hits.sort_values("rank").drop_duplicates(key).set_index(key).join(terms).reset_index()
    collected = pd.to_datetime(hits.collected_at, utc=True).max()
    cutoff = collected - pd.DateOffset(months=C.RECENCY_MONTHS)
    apps["updated_utc"] = cfg["updated"](apps[cfg["updated_key"]] if "updated_key" in cfg else
                                         apps["updated" if name == "google_play_store" else "currentVersionReleaseDate"])
    decisions = [classify(r[cfg["title"]], r[cfg["developer"]], r[cfg["category"]], r[cfg["ratings"]],
                          r["updated_utc"], r.get("description", ""), cutoff) for _, r in apps.iterrows()]
    apps["exclusion_reason"] = [d[0] for d in decisions]
    apps["audit_note"] = [d[1] for d in decisions]
    cols = cfg["keep"] + ["search_terms", "term_ids", "best_rank"]
    eligible = apps[apps.exclusion_reason.eq("")][cols].sort_values(cfg["title"])
    excluded = apps[apps.exclusion_reason.ne("")][cols + ["exclusion_reason", "audit_note"]]
    write_csv(eligible, C.PATHS[cfg["eligible"]])
    if C.MARKET == "br":  # mercados internacionais: motivos só nas métricas, sem arquivo de excluídos
        write_csv(excluded, C.PATHS[cfg["excluded"]])
    counts = excluded.exclusion_reason.value_counts()
    stats = {
        "search_hits": int(len(hits)),
        "duplicates_removed_within_store": int(len(hits) - len(apps)),
        "unique_apps": int(len(apps)),
        "recency_cutoff_utc": cutoff.isoformat(),
        "removed_by_reason": {r: int(counts.get(r, 0)) for r in REASONS},
        "removed_total": int(len(excluded)),
        "eligible": int(len(eligible)),
    }
    update_metrics(f"03_clean_{name}", stats)
    return stats


def main():
    for name, cfg in STORES.items():
        stats = clean_store(name, cfg)
        print(f"\n[{name}] {stats['search_hits']} ocorrências -> {stats['unique_apps']} apps únicos "
              f"-> {stats['eligible']} elegíveis")
        for reason, n in stats["removed_by_reason"].items():
            if n:
                print(f"   - {reason}: {n}")


if __name__ == "__main__":
    main()
