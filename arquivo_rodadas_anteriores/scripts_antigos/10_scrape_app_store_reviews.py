"""Collect a bounded set of public Brazilian App Store RSS reviews for in-scope apps."""
import hashlib
import json
import logging
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd
import requests
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import APP_STORE_REQUEST_DELAY_SECONDS, OUTPUT  # noqa: E402
from review_redaction import redact_text  # noqa: E402

PAGE_LIMIT = 10  # Public customer-review RSS exposes a bounded recent sample.
REVIEW_COLUMNS = ["app_mask_id", "content", "score", "lang", "at"]
MAPPING_COLUMNS = ["app_mask_id", "trackId", "title"]
RSS_URL = "https://itunes.apple.com/br/rss/customerreviews/id={app_id}/sortBy=mostRecent/xml"


def local_text(element, name):
    for child in element.iter():
        if child.tag.rsplit("}", 1)[-1] == name:
            return (child.text or "").strip()
    return ""


def parse_page(xml_text):
    root = ET.fromstring(xml_text)
    parsed = []
    for entry in root.iter():
        if entry.tag.rsplit("}", 1)[-1] != "entry":
            continue
        score = local_text(entry, "rating")
        if not score:
            continue  # The feed's first entry is app metadata, not a review.
        title = local_text(entry, "title")
        body = local_text(entry, "content")
        content = " — ".join(part for part in (title, body) if part)
        parsed.append({
            "content": content,
            "score": int(score),
            "at": local_text(entry, "updated"),
        })
    return parsed


def fetch_page(session, app_id, page):
    params = {"page": page, "l": "pt-BR"}
    response = session.get(RSS_URL.format(app_id=app_id), params=params, timeout=30)
    response.raise_for_status()
    return parse_page(response.text)


def main():
    candidates_path = OUTPUT["apple_candidates"]
    if not candidates_path.exists():
        raise SystemExit("Gere primeiro os candidatos atuais: rode src/05_search_app_store.py e src/08_audit_app_store_candidates.py.")
    candidates = pd.read_csv(candidates_path, encoding="utf-8-sig")
    if candidates.empty:
        raise SystemExit("Nenhum candidato Apple em escopo para coletar avaliações.")

    OUTPUT["apple_reviews"].parent.mkdir(parents=True, exist_ok=True)
    OUTPUT["apple_mapping"].parent.mkdir(parents=True, exist_ok=True)
    try:
        checkpoint_path = OUTPUT["apple_mapping"].parent / "app_store_review_checkpoint.json"
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        checkpoint_path = OUTPUT["apple_mapping"].parent / "app_store_review_checkpoint.json"
        checkpoint = {"completed_track_ids": []}
    completed = set(map(str, checkpoint.get("completed_track_ids", [])))
    reviews = []
    if OUTPUT["apple_reviews"].exists():
        prior = pd.read_csv(OUTPUT["apple_reviews"], encoding="utf-8-sig")
        reviews = prior.reindex(columns=REVIEW_COLUMNS).fillna("").to_dict("records")
    mapping = []
    if OUTPUT["apple_mapping"].exists():
        prior_mapping = pd.read_csv(OUTPUT["apple_mapping"], encoding="utf-8-sig")
        mapping = prior_mapping.reindex(columns=MAPPING_COLUMNS).fillna("").to_dict("records")
    mask_by_track = {str(row["trackId"]): str(row["app_mask_id"]) for row in mapping}

    session = requests.Session()
    session.headers.update({"User-Agent": "OrganizaResearch/1.0 (public App Store RSS review feed)"})
    for idx, app in enumerate(tqdm(candidates.to_dict("records"), desc="Apps Apple", unit="app"), 1):
        track_id = str(app["trackId"])
        if track_id in completed:
            continue
        mask = mask_by_track.get(track_id, f"APPLE_{idx:03d}")
        app_rows = []
        page_keys = set()
        if track_id not in mask_by_track:
            mapping.append({"app_mask_id": mask, "trackId": track_id, "title": app.get("trackName", "")})
            mask_by_track[track_id] = mask
        try:
            for page in range(1, PAGE_LIMIT + 1):
                batch = fetch_page(session, track_id, page)
                if not batch:
                    break
                for item in batch:
                    clean = redact_text(item["content"])
                    stable = "|".join((track_id, clean, str(item["score"]), item["at"]))
                    key = hashlib.sha256(stable.encode("utf-8")).hexdigest()
                    if key in page_keys:
                        continue
                    page_keys.add(key)
                    app_rows.append({
                        "_key": key,
                        "app_mask_id": mask,
                        "content": clean,
                        "score": item["score"],
                        "lang": "pt",
                        "at": item["at"],
                    })
                time.sleep(APP_STORE_REQUEST_DELAY_SECONDS)
        except (requests.RequestException, ET.ParseError, ValueError) as exc:
            tqdm.write(f"{app.get('trackName', track_id)}: erro ao consultar RSS: {exc}")
            if track_id not in completed and track_id in mask_by_track:
                mapping = [row for row in mapping if str(row.get("trackId")) != track_id]
                mask_by_track.pop(track_id, None)
            continue

        existing_keys = set()
        for row in reviews:
            if str(row.get("app_mask_id", "")) == mask:
                signature = "|".join((track_id, str(row.get("content", "")), str(row.get("score", "")), str(row.get("at", ""))))
                existing_keys.add(hashlib.sha256(signature.encode("utf-8")).hexdigest())
        new_rows = [row for row in app_rows if row["_key"] not in existing_keys]
        for row in new_rows:
            row.pop("_key", None)
            reviews.append(row)
        completed.add(track_id)
        checkpoint["completed_track_ids"] = sorted(completed)
        pd.DataFrame(reviews, columns=REVIEW_COLUMNS).to_csv(OUTPUT["apple_reviews"], index=False, encoding="utf-8-sig")
        pd.DataFrame(mapping, columns=MAPPING_COLUMNS).to_csv(OUTPUT["apple_mapping"], index=False, encoding="utf-8-sig")
        checkpoint_path.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2), encoding="utf-8")
        tqdm.write(f"{app.get('trackName', track_id)}: {len(new_rows)} avaliações novas (feed público limitado a até {PAGE_LIMIT} páginas)")
        time.sleep(APP_STORE_REQUEST_DELAY_SECONDS)

    logging.info("Reviews Apple armazenadas: %s", len(reviews))


if __name__ == "__main__":
    main()
