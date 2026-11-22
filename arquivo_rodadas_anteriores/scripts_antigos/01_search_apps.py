"""Find top Google Play results for each configured query and deduplicate by appId."""
import json
import logging
import re
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from tqdm import tqdm
from google_play_scraper import app as play_app, search

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import EXCLUDED_APP_NAME, OUTPUT, REQUEST_DELAY_SECONDS, RESULTS_PER_TERM, SEARCH_TERMS

FINANCIAL_EDUCATION = re.compile(
    r"\b(educacao financeira|educador(?:a)? financeiro|financial education|finance education|"
    r"financial literacy|finance literacy|learn(?:ing)? about money|learn(?:ing)? finance|"
    r"curso de financas|aprender financas|educacao sobre dinheiro)\b"
)
BANK_WORDS = re.compile(r"\b(bank|banco|banking|bancario|credit union|banco digital|conta digital)\b")
BANK_BRANDS = {
    "itau", "nubank", "santander", "bradesco", "banco do brasil", "caixa",
    "c6 bank", "btg pactual", "pagbank", "mercado pago", "picpay", "inter",
}


def normalize(text):
    value = unicodedata.normalize("NFKD", str(text or ""))
    value = value.encode("ascii", "ignore").decode("ascii").casefold()
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def scope_reason(row):
    genre = str(row.get("genre") or "").strip().casefold()
    if genre != "education":
        return f"Categoria fora do escopo (somente Education): {row.get('genre', '')}"
    name = normalize(f"{row.get('title', '')} {row.get('developer', '')}")
    if BANK_WORDS.search(name) or any(f" {brand} " in f" {name} " for brand in BANK_BRANDS):
        return "Banco ou marca bancária; fora do escopo de educação financeira"
    evidence = normalize(f"{row.get('title', '')} {row.get('_description', '')}")
    if not FINANCIAL_EDUCATION.search(evidence):
        return "Título/descrição não confirma conteúdo de educação financeira"
    return ""


def setup_logging():
    OUTPUT["logs"].mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", handlers=[logging.FileHandler(OUTPUT["logs"] / f"search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log", encoding="utf-8"), logging.StreamHandler()])


def call_retry(fn, *args, **kwargs):
    for attempt in range(4):
        try:
            return fn(*args, **kwargs)
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)


def main():
    setup_logging()
    OUTPUT["candidates"].parent.mkdir(parents=True, exist_ok=True)
    collected = []
    collected_at = datetime.now(timezone.utc).isoformat()
    for scope, cfg in SEARCH_TERMS.items():
        for term_id, query in cfg["terms"].items():
            logging.info("Searching %s %s (%s)", scope, term_id, query)
            try:
                results = call_retry(search, query, lang=cfg["lang"], country=cfg["country"], n_hits=RESULTS_PER_TERM)
            except Exception as exc:
                logging.exception("Search failed: %s", exc)
                continue
            for rank, result in enumerate(tqdm(results[:RESULTS_PER_TERM], desc=f"{scope} {term_id}"), 1):
                app_id = result.get("appId")
                if not app_id:
                    continue
                try:
                    details = call_retry(play_app, app_id, lang=cfg["lang"], country=cfg["country"])
                except Exception as exc:
                    logging.warning("Metadata failed for %s: %s", app_id, exc)
                    details = result
                collected.append({"appId": app_id, "title": details.get("title") or result.get("title"), "developer": details.get("developer") or result.get("developer"), "installs": details.get("installs"), "ratings": details.get("ratings"), "reviews": details.get("reviews"), "score": details.get("score"), "genre": details.get("genre"), "inAppProductPrice": details.get("inAppProductPrice"), "updated": details.get("updated"), "url": details.get("url") or result.get("url"), "term_id": term_id, "term": query, "lang": cfg["lang"], "country": cfg["country"], "rank": rank, "collected_at": collected_at, "_description": details.get("description") or result.get("summary") or ""})
                time.sleep(REQUEST_DELAY_SECONDS)
    cols = ["appId", "title", "developer", "installs", "ratings", "reviews", "score", "genre", "inAppProductPrice", "updated", "url", "matched_terms", "matched_scopes", "collected_at"]
    excluded = []
    in_scope = []
    for row in collected:
        if EXCLUDED_APP_NAME in str(row.get("title", "")).casefold() or EXCLUDED_APP_NAME in str(row.get("developer", "")).casefold():
            row["scope_reason"] = "Organiza AI é o produto de referência, não um concorrente"
            excluded.append(row)
            continue
        reason = scope_reason(row)
        if reason:
            row["scope_reason"] = reason
            excluded.append(row)
        else:
            in_scope.append(row)
    collected = in_scope
    if excluded:
        pd.DataFrame(excluded).drop(columns=["_description"], errors="ignore").to_csv(
            OUTPUT["candidates_excluded"], index=False, encoding="utf-8-sig"
        )
    else:
        pd.DataFrame(columns=cols + ["scope_reason"]).to_csv(
            OUTPUT["candidates_excluded"], index=False, encoding="utf-8-sig"
        )
    if collected:
        frame = pd.DataFrame(collected).drop(columns=["_description"], errors="ignore")
        grouped = frame.groupby("appId", as_index=False).agg({"title":"first", "developer":"first", "installs":"first", "ratings":"first", "reviews":"first", "score":"first", "genre":"first", "inAppProductPrice":"first", "updated":"first", "url":"first", "term_id":lambda x: ";".join(dict.fromkeys(x)), "term":lambda x: ";".join(dict.fromkeys(x)), "lang":lambda x: ";".join(dict.fromkeys(x)), "country":lambda x: ";".join(dict.fromkeys(x)), "collected_at":"first"}).rename(columns={"term_id":"matched_terms", "term":"queries", "lang":"matched_languages", "country":"matched_regions"})
        grouped.to_csv(OUTPUT["candidates"], index=False, encoding="utf-8-sig")
        OUTPUT["metrics"].parent.mkdir(parents=True, exist_ok=True)
        metrics = {"collected_at": collected_at, "search_result_rows": len(collected), "unique_apps": len(grouped), "excluded_scope": len(excluded), "results_per_term": RESULTS_PER_TERM, "searches_configured": sum(len(x["terms"]) for x in SEARCH_TERMS.values())}
    else:
        pd.DataFrame(columns=cols).to_csv(OUTPUT["candidates"], index=False, encoding="utf-8-sig")
        metrics = {"collected_at": collected_at, "search_result_rows": 0, "unique_apps": 0, "excluded_organiza_ai": len(excluded), "results_per_term": RESULTS_PER_TERM, "searches_configured": sum(len(x["terms"]) for x in SEARCH_TERMS.values()), "error": "No results; inspect logs/network connectivity."}
    OUTPUT["metrics"].parent.mkdir(parents=True, exist_ok=True)
    OUTPUT["metrics"].write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    logging.info("Saved %s unique candidates", metrics["unique_apps"])

if __name__ == "__main__":
    main()





