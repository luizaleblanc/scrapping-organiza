"""Collect approved Google Play reviews; store only allowlisted anonymous fields."""
import json, socket, sys, time
from pathlib import Path
import pandas as pd
from tqdm import tqdm
from google_play_scraper import Sort, reviews

# google-play-scraper calls urllib without a timeout argument.
socket.setdefaulttimeout(30)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import OUTPUT, REQUEST_DELAY_SECONDS

REVIEW_COLUMNS = ["app_mask_id", "content", "score", "lang", "at"]
MAPPING_COLUMNS = ["app_mask_id", "appId", "title"]


def main():
    OUTPUT["logs"].mkdir(parents=True, exist_ok=True)
    OUTPUT["reviews"].parent.mkdir(parents=True, exist_ok=True)
    OUTPUT["mapping"].parent.mkdir(parents=True, exist_ok=True)
    screening = pd.read_csv(OUTPUT["screening"])
    approved = screening[
        (screening["automatic_criteria_pass"] == True)
        & screening["criterion_1_decision"].astype(str).str.casefold().eq("yes")
        & screening["criterion_5_decision"].astype(str).str.casefold().eq("yes")
    ]
    if approved.empty:
        raise SystemExit(
            "No apps approved. Set criterion_1_decision and criterion_5_decision to yes "
            "for manually approved rows in apps_screening.csv."
        )

    checkpoint_path = OUTPUT["mapping"].parent / "review_checkpoint.json"
    try:
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        checkpoint = {"completed_app_ids": []}
    completed = set(map(str, checkpoint.get("completed_app_ids", [])))
    if OUTPUT["reviews"].exists():
        stored = pd.read_csv(OUTPUT["reviews"], encoding="utf-8-sig")
        anonymized = stored.reindex(columns=REVIEW_COLUMNS).fillna("").to_dict("records")
    else:
        anonymized = []
    if OUTPUT["mapping"].exists():
        stored_mapping = pd.read_csv(OUTPUT["mapping"], encoding="utf-8-sig")
        mapping = stored_mapping.reindex(columns=MAPPING_COLUMNS).fillna("").to_dict("records")
    else:
        mapping = []

    for idx, app_row in enumerate(tqdm(approved.to_dict("records"), desc="Apps", unit="app"), 1):
        app_id = str(app_row["appId"])
        if app_id in completed:
            continue
        mask = f"APP_{idx:03d}"
        mapping.append({"app_mask_id": mask, "appId": app_id, "title": app_row["title"]})
        english = "en" in str(app_row.get("matched_languages", "")).split(";")
        lang, country = ("en", "us") if english else ("pt", "br")
        expected = pd.to_numeric(app_row.get("reviews"), errors="coerce")
        expected = int(expected) if pd.notna(expected) else None
        token = None
        collected_for_app = []
        with tqdm(total=expected, desc=mask, unit="review", leave=False) as progress:
            while True:
                batch, token = reviews(
                    app_id, lang=lang, country=country, sort=Sort.NEWEST,
                    count=200, continuation_token=token,
                )
                for item in batch:
                    # Explicit allowlist: names, images, review IDs, and other
                    # personal fields are discarded and never written to disk.
                    collected_for_app.append({
                        "app_mask_id": mask,
                        "content": item.get("content", ""),
                        "score": item.get("score"),
                        "lang": lang,
                        "at": str(item.get("at", "")),
                    })
                progress.update(len(batch))
                if expected is not None and len(collected_for_app) >= expected:
                    break
                if not batch and token is None and not collected_for_app and expected:
                    raise RuntimeError(
                        f"Google Play returned no reviews for {app_row['title']} although metadata lists "
                        f"{expected}. Check the connection; completed apps are checkpointed for resume."
                    )
                # google-play-scraper always returns a continuation-token object;
                # end-of-pagination is represented by token.token being None.
                has_more_pages = token is not None and getattr(token, "token", None) is not None
                if not has_more_pages:
                    if expected is not None and len(collected_for_app) < expected:
                        tqdm.write(
                            f"Note: Google Play exposed {len(collected_for_app)} review texts for "
                            f"{app_row['title']} while app metadata lists {expected}; continuing with available reviews."
                        )
                    break
                time.sleep(REQUEST_DELAY_SECONDS)

        anonymized.extend(collected_for_app)
        completed.add(app_id)
        checkpoint["completed_app_ids"] = sorted(completed)
        pd.DataFrame(anonymized, columns=REVIEW_COLUMNS).to_csv(
            OUTPUT["reviews"], index=False, encoding="utf-8-sig"
        )
        pd.DataFrame(mapping, columns=MAPPING_COLUMNS).to_csv(
            OUTPUT["mapping"], index=False, encoding="utf-8-sig"
        )
        checkpoint_path.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2), encoding="utf-8")
        tqdm.write(f"{app_row['title']}: saved {len(collected_for_app)} reviews")

    OUTPUT["metrics"].parent.mkdir(parents=True, exist_ok=True)
    try:
        metrics = json.loads(OUTPUT["metrics"].read_text(encoding="utf-8"))
    except (OSError, ValueError):
        metrics = {}
    metrics["reviews_collected"] = len(anonymized)
    OUTPUT["metrics"].write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
