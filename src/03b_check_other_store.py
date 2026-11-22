"""Etapa 3b — Critério 4: o app elegível em uma loja está DISPONÍVEL na outra?

O critério 4 do artigo pede disponibilidade nas duas lojas, não que o app apareça no
top 30 das strings nas duas. Para cada app elegível que não tem par na outra loja,
procura o mesmo app pelo nome na outra loja (Brasil) e:
  - só considera resultados com a MESMA MARCA (nome-base do título);
  - aplica à versão encontrada exatamente as mesmas regras (rules.classify);
  - se elegível, acrescenta ao apps_eligible.csv da outra loja com
    discovery_source = "availability_check" (a origem fica rastreável).
O pareamento final continua sendo feito (e conferido) na etapa 4.
Saída extra: data/apps_nas_duas_lojas/availability_check_audit.csv
"""
import importlib
import re
import sys
import time
from pathlib import Path

import pandas as pd
import requests
from google_play_scraper import app as play_app, search as play_search

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
from rules import classify, update_metrics, write_csv  # noqa: E402
from text_norm import brand  # noqa: E402

page_updated = importlib.import_module("01_search_google_play").page_updated
AUDIT = C.CROSS_DIR / "availability_check_audit.csv"


def as_lookup(title):
    try:
        r = requests.get("https://itunes.apple.com/search", params={
            "term": title, "entity": "software", "country": C.COUNTRY, "limit": 10}, timeout=25)
        return r.json().get("results", [])
    except (requests.RequestException, ValueError):
        return []


def featured_app_id(title):
    """A google-play-scraper devolve o 1º resultado (destaque) sem appId. Recupera o id
    pelo primeiro link 'details?id=' da página pública de busca da Play Store."""
    try:
        html = requests.get("https://play.google.com/store/search", params={
            "q": title, "c": "apps", "hl": "pt_BR", "gl": "BR"}, timeout=30).text
    except requests.RequestException:
        return None
    m = re.search(r"/store/apps/details\?id=([\w.]+)", html)
    return m.group(1) if m else None


def gp_lookup(title):
    try:
        results = play_search(title, lang=C.LANG, country=C.COUNTRY, n_hits=10)
    except Exception:
        return []
    for r in results:
        if not r.get("appId"):
            r["appId"] = featured_app_id(title)
    return results


def main():
    gp = pd.read_csv(C.PATHS["gp_eligible"], encoding="utf-8-sig")
    a_s = pd.read_csv(C.PATHS["as_eligible"], encoding="utf-8-sig")
    for df in (gp, a_s):
        if "discovery_source" not in df:
            df["discovery_source"] = "search_strings"
    gp = gp[gp.discovery_source.eq("search_strings")]
    a_s = a_s[a_s.discovery_source.eq("search_strings")]
    cutoff = pd.Timestamp.now(tz="UTC") - pd.DateOffset(months=C.RECENCY_MONTHS)
    gp_brands, as_brands = set(gp.title.map(brand)), set(a_s.trackName.map(brand))
    audit, add_gp, add_as = [], [], []

    # Google Play elegível -> procura na App Store
    for g in gp[~gp.title.map(brand).isin(as_brands)].itertuples():
        for res in as_lookup(g.title):
            if brand(res.get("trackName")) != brand(g.title) or res.get("trackId") in set(a_s.trackId):
                continue
            upd = pd.to_datetime(res.get("currentVersionReleaseDate"), utc=True, errors="coerce")
            reason, note = classify(res.get("trackName"), res.get("artistName"),
                                    res.get("primaryGenreName"), res.get("userRatingCount"), upd,
                                    res.get("description", ""), cutoff)
            audit.append({"source_store": "google_play_store", "source_id": g.appId, "source_title": g.title,
                          "found_store": "app_store", "found_id": res["trackId"], "found_title": res["trackName"],
                          "found_developer": res.get("artistName"), "exclusion_reason": reason, "audit_note": note})
            if not reason:
                add_as.append({"trackId": res["trackId"], "bundleId": res.get("bundleId"),
                               "trackName": res["trackName"], "artistName": res.get("artistName"),
                               "primaryGenreName": res.get("primaryGenreName"),
                               "averageUserRating": res.get("averageUserRating"),
                               "userRatingCount": res.get("userRatingCount"), "updated_utc": upd,
                               "trackViewUrl": res.get("trackViewUrl"), "search_terms": "",
                               "term_ids": "", "best_rank": None, "discovery_source": "availability_check"})
            break  # só o primeiro resultado com a mesma marca
        time.sleep(C.APP_STORE_DELAY_SECONDS)

    # App Store elegível -> procura na Google Play
    for a in a_s[~a_s.trackName.map(brand).isin(gp_brands)].itertuples():
        for res in gp_lookup(a.trackName):
            if not res.get("appId") or brand(res.get("title")) != brand(a.trackName) or res["appId"] in set(gp.appId):
                continue
            try:
                d = play_app(res["appId"], lang=C.LANG, country=C.COUNTRY)
            except Exception:
                d = res
            ts = d.get("updated") or page_updated(res["appId"])
            upd = pd.to_datetime(ts, unit="s", utc=True) if ts else pd.NaT
            reason, note = classify(d.get("title"), d.get("developer"), d.get("genre"), d.get("ratings"),
                                    upd, d.get("description", ""), cutoff)
            audit.append({"source_store": "app_store", "source_id": a.trackId, "source_title": a.trackName,
                          "found_store": "google_play_store", "found_id": res["appId"], "found_title": d.get("title"),
                          "found_developer": d.get("developer"), "exclusion_reason": reason, "audit_note": note})
            if not reason:
                add_gp.append({"appId": res["appId"], "title": d.get("title"), "developer": d.get("developer"),
                               "genre": d.get("genre"), "installs": d.get("installs"), "ratings": d.get("ratings"),
                               "reviews": d.get("reviews"), "score": d.get("score"), "updated_utc": upd,
                               "url": d.get("url"), "search_terms": "", "term_ids": "", "best_rank": None,
                               "discovery_source": "availability_check"})
            break
        time.sleep(C.REQUEST_DELAY_SECONDS)

    write_csv(pd.concat([gp, pd.DataFrame(add_gp)], ignore_index=True), C.PATHS["gp_eligible"])
    write_csv(pd.concat([a_s, pd.DataFrame(add_as)], ignore_index=True), C.PATHS["as_eligible"])
    write_csv(pd.DataFrame(audit), AUDIT)
    update_metrics("03b_availability_check", {
        "counterparts_checked": len(audit),
        "added_to_google_play_eligible": len(add_gp), "added_to_app_store_eligible": len(add_as),
    })
    print(f"Verificados {len(audit)} pares; adicionados GP={len(add_gp)} AS={len(add_as)}")
    if audit:
        print(pd.DataFrame(audit)[["source_title", "found_store", "found_title", "found_developer",
                                   "exclusion_reason"]].to_string(index=False))


if __name__ == "__main__":
    main()
