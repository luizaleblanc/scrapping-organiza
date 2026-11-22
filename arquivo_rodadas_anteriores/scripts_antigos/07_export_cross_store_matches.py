"""Export Google Play apps also found in Apple App Store search checks."""
import re
import sys
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import OUTPUT  # noqa: E402


def normalize(value):
    if pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKD", str(value))
    text = text.encode("ascii", "ignore").decode("ascii").casefold()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def exact_candidate(title, developer, indexed_candidates):
    title_key = normalize(title)
    matches = indexed_candidates.get(title_key, [])
    if not matches:
        return None, 0.0
    developer_key = normalize(developer)
    scored = []
    for candidate in matches:
        seller_similarity = SequenceMatcher(
            None, developer_key, normalize(candidate.get("artistName"))
        ).ratio()
        scored.append((seller_similarity, candidate))
    seller_similarity, best = max(scored, key=lambda item: item[0])
    return best, seller_similarity


def main():
    screening_path = OUTPUT["screening"]
    apple_path = OUTPUT["apple_candidates"]
    if not screening_path.exists() or not apple_path.exists():
        raise SystemExit("Execute a triagem Google Play e a busca App Store antes desta etapa.")

    screening = pd.read_csv(screening_path, encoding="utf-8-sig")
    apple = pd.read_csv(apple_path, encoding="utf-8-sig")
    required_screening = {"appId", "title", "developer", "apple_store_exists", "apple_matched_title"}
    missing = required_screening - set(screening.columns)
    if missing:
        raise SystemExit(f"A triagem está sem colunas necessárias: {', '.join(sorted(missing))}")

    indexed_candidates = {}
    for candidate in apple.to_dict("records"):
        indexed_candidates.setdefault(normalize(candidate.get("trackName")), []).append(candidate)

    found = screening[
        screening["apple_store_exists"].astype(str).str.casefold().eq("true")
    ].copy()
    rows = []
    for app in found.to_dict("records"):
        apple_title = app.get("apple_matched_title") or ""
        candidate, seller_similarity = exact_candidate(
            apple_title or app.get("title"), app.get("developer"), indexed_candidates
        )
        automatic_pass = str(app.get("automatic_criteria_pass", "")).casefold() == "true"
        manual_1 = str(app.get("criterion_1_decision", "")).casefold()
        manual_5 = str(app.get("criterion_5_decision", "")).casefold()
        approved = automatic_pass and manual_1 == "yes" and manual_5 == "yes"
        exact_export_match = candidate is not None
        if exact_export_match and seller_similarity >= 0.8:
            confidence = "strong_title_and_seller_match"
        elif exact_export_match:
            confidence = "exact_title_seller_needs_review"
        else:
            confidence = "apple_lookup_match_needs_manual_review"

        lang_values = str(app.get("matched_languages", "")).split(";")
        lookup_region = "br" if "pt" in lang_values else "us"
        rows.append({
            "google_play_app_id": app.get("appId"),
            "google_play_title": app.get("title"),
            "google_play_developer": app.get("developer"),
            "google_play_regions": app.get("matched_regions"),
            "google_play_url": app.get("url"),
            "apple_lookup_storefront": lookup_region,
            "apple_lookup_matched_title": apple_title,
            "apple_lookup_flag": app.get("apple_store_exists"),
            "apple_candidate_exact_title_match": exact_export_match,
            "apple_track_id": candidate.get("trackId") if candidate else "",
            "apple_bundle_id": candidate.get("bundleId") if candidate else "",
            "apple_title": candidate.get("trackName") if candidate else apple_title,
            "apple_developer": candidate.get("artistName") if candidate else "",
            "apple_genre": candidate.get("primaryGenreName") if candidate else "",
            "apple_rating": candidate.get("averageUserRating") if candidate else "",
            "apple_rating_count": candidate.get("userRatingCount") if candidate else "",
            "apple_regions_in_search_export": candidate.get("matched_regions") if candidate else "",
            "apple_url": candidate.get("trackViewUrl") if candidate else "",
            "seller_similarity": round(seller_similarity, 3) if candidate else "",
            "match_confidence": confidence,
            "current_scrape_sample_approved": approved,
            "manual_identity_review_required": confidence != "strong_title_and_seller_match",
        })

    result = pd.DataFrame(rows)
    output_path = OUTPUT["screening"].parent / "apps_in_both_stores.csv"
    result.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"Apps marcados como encontrados nas duas lojas: {len(result)}")
    print(f"Correspondência exata também no CSV da App Store: {int(result['apple_candidate_exact_title_match'].sum())}")
    print(f"Incluídos na amostra aprovada atual: {int(result['current_scrape_sample_approved'].sum())}")
    print(f"Arquivo salvo: {output_path}")


if __name__ == "__main__":
    main()
