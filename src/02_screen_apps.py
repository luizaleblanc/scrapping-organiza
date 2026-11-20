"""Apply reproducible automatic screens and leave subjective decisions for review."""
import json, logging, sys, time
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import requests
from tqdm import tqdm
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import OUTPUT, RECENT_MONTHS, REQUEST_DELAY_SECONDS


def app_store_exists(title, developer, country):
    """Use Apple's public search endpoint for existence only; never fetch reviews."""
    query = " ".join(x for x in [title, developer] if x)
    try:
        response = requests.get("https://itunes.apple.com/search", params={"term": query, "entity": "software", "country": country, "limit": 25}, timeout=20)
        response.raise_for_status()
        hits = response.json().get("results", [])
        name = (title or "").casefold()
        matched = next((x for x in hits if name and (name in x.get("trackName", "").casefold() or x.get("trackName", "").casefold() in name)), None)
        return bool(matched), (matched or {}).get("trackName", "")
    except requests.RequestException as exc:
        logging.warning("Apple search failed for %s: %s", title, exc)
        return None, ""


def parse_updated(value):
    """Play Scraper returns Unix seconds; accept datetime-like values too."""
    if pd.isna(value):
        return pd.NaT
    numeric = pd.to_numeric(value, errors="coerce")
    if pd.notna(numeric):
        return pd.to_datetime(numeric, unit="s", utc=True, errors="coerce")
    return pd.to_datetime(value, utc=True, errors="coerce")


def main():
    OUTPUT["logs"].mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=OUTPUT["logs"] / f"screen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", encoding="utf-8")
    if not OUTPUT["candidates"].exists():
        raise FileNotFoundError(f"Run search first: {OUTPUT['candidates']}")
    df = pd.read_csv(OUTPUT["candidates"])
    cached = {}
    if OUTPUT["screening"].exists():
        old = pd.read_csv(OUTPUT["screening"])
        if {"appId", "apple_store_exists", "apple_matched_title"}.issubset(old.columns):
            cached = old.set_index("appId")[["apple_store_exists", "apple_matched_title"]].to_dict("index")
    cutoff = pd.Timestamp.now(tz="UTC") - pd.DateOffset(months=RECENT_MONTHS)
    rows = []
    for row in tqdm(df.to_dict("records"), desc="Screening apps"):
        genre = str(row.get("genre") or "").strip().casefold()
        category_ok = genre in {"finance", "finanças"}
        reviews_count = pd.to_numeric(row.get("reviews"), errors="coerce")
        updated = parse_updated(row.get("updated"))
        recent_ok = bool(pd.notna(updated) and updated >= cutoff)
        lang = str(row.get("matched_languages", ""))
        country = "br" if "pt" in lang.split(";") else "us"
        saved = cached.get(row.get("appId"))
        if saved:
            apple = saved["apple_store_exists"]
            apple = None if pd.isna(apple) else bool(apple)
            apple_name = saved["apple_matched_title"] if pd.notna(saved["apple_matched_title"]) else ""
        else:
            apple, apple_name = app_store_exists(str(row.get("title", "")), str(row.get("developer", "")), country)
            time.sleep(REQUEST_DELAY_SECONDS)
        rows.append({**row, "updated_utc": updated.isoformat() if pd.notna(updated) else "", "category_ok": category_ok, "reviews_present_ok": bool(pd.notna(reviews_count) and reviews_count > 0), "apple_store_exists": apple, "apple_matched_title": apple_name, "updated_in_last_12_months": recent_ok, "criterion_1_personal_budget_focus_manual": "REVIEW_REQUIRED", "criterion_1_decision": "", "criterion_5_b2c_manual": "REVIEW_REQUIRED", "criterion_5_decision": "", "automatic_criteria_pass": bool(category_ok and pd.notna(reviews_count) and reviews_count > 0 and recent_ok and apple is True), "screened_at": datetime.now(timezone.utc).isoformat()})
    result = pd.DataFrame(rows)
    result.to_csv(OUTPUT["screening"], index=False, encoding="utf-8-sig")
    metrics = {}
    if OUTPUT["metrics"].exists():
        try: metrics = json.loads(OUTPUT["metrics"].read_text(encoding="utf-8"))
        except (ValueError, OSError): pass
    metrics.update({"screened_apps": len(result), "category_pass": int(result["category_ok"].sum()) if len(result) else 0, "reviews_present_pass": int(result["reviews_present_ok"].sum()) if len(result) else 0, "apple_presence_confirmed": int((result["apple_store_exists"] == True).sum()) if len(result) else 0, "recent_update_pass": int(result["updated_in_last_12_months"].sum()) if len(result) else 0, "automatic_screen_pass": int(result["automatic_criteria_pass"].sum()) if len(result) else 0, "manual_review_required": len(result), "screening_note": "Manual criteria 1 and 5 must be reviewed; Apple search is an approximate existence check. No reviews were retrieved from Apple."})
    OUTPUT["metrics"].write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__": main()
