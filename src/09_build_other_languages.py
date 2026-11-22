"""Etapa 9 — Outros idiomas (inglês: EUA; espanhol: Espanha e México).

Pré-requisito: rodar as etapas 1 a 4 em cada mercado extra, por exemplo
    $env:MARKET = "us"; python src/01_search_google_play.py  (... até 04)
Depois, rode este script SEM MARKET (ou com MARKET=br).

Gera dois arquivos em data/brasil/apps_nas_duas_lojas/:
  apps_both_stores_outros_idiomas.csv  as apps da amostra original (Brasil), com colunas
      por mercado: reviews encontradas em cada loja naquele idioma (contagem até o teto
      REVIEW_CAP), se a app fica nas duas lojas naquele idioma e se a busca traduzida
      do mercado também a encontrou.
  apps_novos_outros_idiomas.csv        apps que as buscas traduzidas acharam, que passam
      pelos mesmos critérios (etapas 3 a 4 do mercado) e que NÃO estão na amostra original.
Nenhuma review é gravada aqui: só contagens.
"""
import sys
import time
from pathlib import Path

import pandas as pd
import requests
from google_play_scraper import Sort, reviews

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
from rules import update_metrics, write_csv  # noqa: E402

REVIEW_CAP = 500  # Apple RSS entrega no máximo 500 (10 páginas x 50); mesmo teto na Google Play
FEED = "https://itunes.apple.com/{country}/rss/customerreviews/page={page}/id={track_id}/sortby=mostrecent/json"


def market_both(m):
    path = C.market_dir(m) / "apps_nas_duas_lojas" / "apps_both_stores.csv"
    return pd.read_csv(path, encoding="utf-8-sig") if path.exists() else None


def gp_count(app_id, lang, country):
    total, token = 0, None
    while total < REVIEW_CAP:
        try:
            batch, token = reviews(app_id, lang=lang, country=country, sort=Sort.NEWEST,
                                   count=min(200, REVIEW_CAP - total), continuation_token=token)
        except Exception:
            return None
        total += sum(1 for r in batch if r.get("content"))
        if not batch or token is None or token.token is None:
            break
        time.sleep(C.REQUEST_DELAY_SECONDS)
    return min(total, REVIEW_CAP)


def as_count(track_id, country):
    total = 0
    for page in range(1, 11):
        try:
            r = requests.get(FEED.format(country=country, page=page, track_id=int(track_id)), timeout=25)
            entries = r.json().get("feed", {}).get("entry", []) if r.ok else []
        except (requests.RequestException, ValueError):
            return None if page == 1 else total
        entries = [entries] if isinstance(entries, dict) else entries
        n = sum(1 for e in entries if "im:rating" in e)
        total += n
        if n < 50:
            break
        time.sleep(1)
    return total


def main():
    if C.MARKET != "br":
        raise SystemExit("Rode este script sem MARKET (ou MARKET=br).")
    base = pd.read_csv(C.BR_BOTH_STORES, encoding="utf-8-sig")
    gp_ids, as_ids = set(base.gp_app_id), set(base.as_track_id.astype(int))
    out, new_rows, stats = base.copy(), [], {}

    for m in C.EXTRA_MARKETS:
        lang = C.MARKETS[m][0]
        found = market_both(m)
        if found is None:
            print(f"[{m}] etapas 1 a 4 ainda não rodadas; coluna de busca fica vazia")
        found_gp = set(found.gp_app_id) if found is not None else set()
        found_as = set(found.as_track_id.astype(int)) if found is not None else set()
        gp_n, as_n = [], []
        for r in base.itertuples():
            gp_n.append(gp_count(r.gp_app_id, lang, m))
            as_n.append(as_count(r.as_track_id, m))
            print(f"[{m}] {r.unified_name[:40]:40} GP={gp_n[-1]} AS={as_n[-1]}")
        out[f"gp_reviews_{m}_{lang}"] = gp_n
        out[f"as_reviews_{m}_{lang}"] = as_n
        out[f"nas_duas_lojas_{m}_{lang}"] = [bool(g and a) for g, a in zip(gp_n, as_n)]
        out[f"achada_na_busca_{m}"] = (base.gp_app_id.isin(found_gp) | base.as_track_id.astype(int).isin(found_as)
                                       if found is not None else pd.NA)
        if found is not None:
            novos = found[~found.gp_app_id.isin(gp_ids) & ~found.as_track_id.astype(int).isin(as_ids)]
            new_rows.append(novos.assign(mercado=m, idioma=lang))
        stats[m] = {"amostra_com_reviews_nas_duas_lojas": int(out[f"nas_duas_lojas_{m}_{lang}"].sum()),
                    "apps_nas_duas_lojas_na_busca": None if found is None else int(len(found)),
                    "apps_novos": 0 if found is None else int(len(new_rows[-1]))}

    write_csv(out, C.MULTILANG_EXISTING)
    if new_rows:
        allnew = pd.concat(new_rows, ignore_index=True)
        agg = (allnew.groupby("gp_app_id")
               .agg(mercados=("mercado", lambda s: ";".join(dict.fromkeys(s))),
                    idiomas=("idioma", lambda s: ";".join(dict.fromkeys(s)))))
        novos = (allnew.drop_duplicates("gp_app_id").drop(columns=["mercado", "idioma"])
                 .set_index("gp_app_id").join(agg).reset_index().sort_values("unified_name"))
    else:
        novos = pd.DataFrame()
    write_csv(novos, C.MULTILANG_NEW)
    update_metrics("09_outros_idiomas", {"review_cap": REVIEW_CAP, "por_mercado": stats,
                                         "apps_novos_unicos": int(len(novos))})
    print(f"\n{C.MULTILANG_EXISTING}\n{C.MULTILANG_NEW} ({len(novos)} apps novos)")
    print(stats)


if __name__ == "__main__":
    main()
