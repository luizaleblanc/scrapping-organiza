"""Discover financial-education apps in the Brazilian App Store."""
import logging
import re
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (  # noqa: E402
    APP_STORE_BRAND_QUERIES,
    APP_STORE_REQUEST_DELAY_SECONDS,
    OUTPUT,
    RESULTS_PER_TERM,
    APP_STORE_SEARCH_TERMS as SEARCH_TERMS,
)

API_URL = "https://itunes.apple.com/search"
FINANCIAL_EDUCATION = re.compile(
    r"\b(educacao financeira|educador(?:a)? financeiro|financial education|finance education|"
    r"financial literacy|finance literacy|learn(?:ing)? about money|learn(?:ing)? finance|"
    r"curso de financas|aprender financas|educacao sobre dinheiro)\b"
)
BANK_TERMS = re.compile(
    r"\b(bank|banking|banco|bancos|bancario|credit union|digital bank|banco digital|conta digital)\b"
)
BANK_BRANDS = {
    "itau", "nubank", "santander", "bradesco", "banco do brasil", "caixa",
    "c6 bank", "btg pactual", "pagbank", "mercado pago", "picpay", "inter",
    "chase", "wells fargo", "bank of america", "capital one", "revolut", "monzo",
}


def normalize(value):
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = value.encode("ascii", "ignore").decode("ascii").casefold()
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def scope_reason(row):
    if str(row.get("primaryGenreName", "")).casefold() != "education":
        return f"Categoria fora do escopo (somente Education): {row.get('primaryGenreName', '')}"
    title, seller = normalize(row.get("trackName")), normalize(row.get("artistName"))
    title_padded, seller_padded = f" {title} ", f" {seller} "
    if BANK_TERMS.search(title) or BANK_TERMS.search(seller) or any(
        f" {brand} " in title_padded or f" {brand} " in seller_padded for brand in BANK_BRANDS
    ):
        return "Banco/serviço bancário; fora do escopo de educação financeira"
    if not FINANCIAL_EDUCATION.search(title):
        return "Título não indica educação financeira explicitamente"
    return ""
HIT_COLUMNS = [
    "trackId", "bundleId", "trackName", "artistName", "primaryGenreName",
    "averageUserRating", "userRatingCount", "version",
    "currentVersionReleaseDate", "releaseDate", "price", "currency",
    "trackViewUrl", "term_id", "term", "scope", "lang", "country",
    "rank", "collected_at",
]


def search_with_retry(query, country):
    params = {
        "term": query,
        "entity": "software",
        "country": country,
        "limit": RESULTS_PER_TERM,
    }
    last_error = None
    for attempt in range(4):
        try:
            response = requests.get(API_URL, params=params, timeout=25)
            response.raise_for_status()
            return response.json().get("results", [])
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            if attempt < 3:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"Apple search failed for {query!r} in {country}: {last_error}")


def configured_searches():
    for scope, cfg in SEARCH_TERMS.items():
        for term_id, query in cfg["terms"].items():
            yield scope, cfg["lang"], cfg["country"], term_id, query
    for index, query in enumerate(APP_STORE_BRAND_QUERIES, 1):
        yield "named_br", "pt", "br", f"B{index:02d}", query


def main():
    # This file keeps the unfiltered store-search results. A separate audit
    # produces candidates.csv so re-running search cannot overwrite the curated list.
    output_path = OUTPUT["apple_candidates_raw"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    hits_path = OUTPUT["apple_hits"]
    hits_path.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT["logs"].mkdir(parents=True, exist_ok=True)
    log_path = OUTPUT["logs"] / f"app_store_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(log_path, encoding="utf-8"), logging.StreamHandler()],
    )

    collected_at = datetime.now(timezone.utc).isoformat()
    rows = []
    for scope, lang, country, term_id, query in tqdm(
        list(configured_searches()), desc="App Store searches", unit="search"
    ):
        try:
            results = search_with_retry(query, country)
        except RuntimeError as exc:
            logging.warning("%s", exc)
            time.sleep(APP_STORE_REQUEST_DELAY_SECONDS)
            continue

        for rank, result in enumerate(results[:RESULTS_PER_TERM], 1):
            rows.append({
                **{column: result.get(column) for column in HIT_COLUMNS[:13]},
                "term_id": term_id,
                "term": query,
                "scope": scope,
                "lang": lang,
                "country": country,
                "rank": rank,
                "collected_at": collected_at,
            })
        logging.info("%s/%s %s: %s results", country, term_id, query, len(results))
        time.sleep(APP_STORE_REQUEST_DELAY_SECONDS)

    all_hits = pd.DataFrame(rows, columns=HIT_COLUMNS)
    if not all_hits.empty:
        all_hits["scope_reason"] = all_hits.apply(scope_reason, axis=1)
        excluded = all_hits[all_hits["scope_reason"].ne("")].copy()
        hits = all_hits[all_hits["scope_reason"].eq("")].drop(columns="scope_reason").copy()
    else:
        excluded = pd.DataFrame(columns=HIT_COLUMNS + ["scope_reason"])
        hits = all_hits
    all_hits.to_csv(OUTPUT["apple_hits_all"], index=False, encoding="utf-8-sig")
    hits.to_csv(hits_path, index=False, encoding="utf-8-sig")
    excluded.to_csv(OUTPUT["apple_hits_excluded"], index=False, encoding="utf-8-sig")

    if hits.empty:
        candidates = pd.DataFrame(columns=[
            "trackId", "bundleId", "trackName", "artistName", "primaryGenreName",
            "averageUserRating", "userRatingCount", "version",
            "currentVersionReleaseDate", "releaseDate", "price", "currency",
            "trackViewUrl", "matched_terms", "matched_scopes", "matched_regions",
            "best_rank", "collected_at",
        ])
    else:
        candidates = hits.dropna(subset=["trackId"]).groupby("trackId", as_index=False).agg({
            "bundleId": "first",
            "trackName": "first",
            "artistName": "first",
            "primaryGenreName": "first",
            "averageUserRating": "first",
            "userRatingCount": "first",
            "version": "first",
            "currentVersionReleaseDate": "first",
            "releaseDate": "first",
            "price": "first",
            "currency": "first",
            "trackViewUrl": "first",
            "term": lambda values: ";".join(dict.fromkeys(map(str, values))),
            "scope": lambda values: ";".join(dict.fromkeys(map(str, values))),
            "country": lambda values: ";".join(dict.fromkeys(map(str, values))),
            "rank": "min",
            "collected_at": "first",
        }).rename(columns={
            "term": "matched_terms",
            "scope": "matched_scopes",
            "country": "matched_regions",
            "rank": "best_rank",
        })
    candidates.to_csv(output_path, index=False, encoding="utf-8-sig")
    logging.info(
        "Apple search returned %s raw hits; %s in-scope hits, %s excluded, %s unique candidates. Files: %s, %s, %s, %s",
        len(all_hits), len(hits), len(excluded), len(candidates),
        OUTPUT["apple_hits_all"], hits_path, OUTPUT["apple_hits_excluded"], output_path,
    )


if __name__ == "__main__":
    main()
