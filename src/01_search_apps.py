"""Find top Google Play results for each configured query and deduplicate by appId."""
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from tqdm import tqdm
from google_play_scraper import app as play_app, search

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import EXCLUDED_APP_NAME, OUTPUT, REQUEST_DELAY_SECONDS, RESULTS_PER_TERM, SEARCH_TERMS


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
                collected.append({"appId": app_id, "title": details.get("title") or result.get("title"), "developer": details.get("developer") or result.get("developer"), "installs": details.get("installs"), "ratings": details.get("ratings"), "reviews": details.get("reviews"), "score": details.get("score"), "genre": details.get("genre"), "inAppProductPrice": details.get("inAppProductPrice"), "updated": details.get("updated"), "url": details.get("url") or result.get("url"), "term_id": term_id, "term": query, "lang": cfg["lang"], "country": cfg["country"], "rank": rank, "collected_at": collected_at})
                time.sleep(REQUEST_DELAY_SECONDS)
    cols = ["appId", "title", "developer", "installs", "ratings", "reviews", "score", "genre", "inAppProductPrice", "updated", "url", "matched_terms", "matched_scopes", "collected_at"]
    excluded = [x for x in collected if EXCLUDED_APP_NAME in str(x.get("title", "")).casefold() or EXCLUDED_APP_NAME in str(x.get("developer", "")).casefold()]
    collected = [x for x in collected if x not in excluded]
    if collected:
        frame = pd.DataFrame(collected)
        grouped = frame.groupby("appId", as_index=False).agg({"title":"first", "developer":"first", "installs":"first", "ratings":"first", "reviews":"first", "score":"first", "genre":"first", "inAppProductPrice":"first", "updated":"first", "url":"first", "term_id":lambda x: ";".join(dict.fromkeys(x)), "term":lambda x: ";".join(dict.fromkeys(x)), "lang":lambda x: ";".join(dict.fromkeys(x)), "country":lambda x: ";".join(dict.fromkeys(x)), "collected_at":"first"}).rename(columns={"term_id":"matched_terms", "term":"queries", "lang":"matched_languages", "country":"matched_regions"})
        grouped.to_csv(OUTPUT["candidates"], index=False, encoding="utf-8-sig")
        OUTPUT["metrics"].parent.mkdir(parents=True, exist_ok=True)
        metrics = {"collected_at": collected_at, "search_result_rows": len(collected), "unique_apps": len(grouped), "excluded_organiza_ai": len(excluded), "results_per_term": RESULTS_PER_TERM, "searches_configured": sum(len(x["terms"]) for x in SEARCH_TERMS.values())}
    else:
        pd.DataFrame(columns=cols).to_csv(OUTPUT["candidates"], index=False, encoding="utf-8-sig")
        metrics = {"collected_at": collected_at, "search_result_rows": 0, "unique_apps": 0, "excluded_organiza_ai": len(excluded), "results_per_term": RESULTS_PER_TERM, "searches_configured": sum(len(x["terms"]) for x in SEARCH_TERMS.values()), "error": "No results; inspect logs/network connectivity."}
    OUTPUT["metrics"].parent.mkdir(parents=True, exist_ok=True)
    OUTPUT["metrics"].write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    logging.info("Saved %s unique candidates", metrics["unique_apps"])

if __name__ == "__main__":
    main()





