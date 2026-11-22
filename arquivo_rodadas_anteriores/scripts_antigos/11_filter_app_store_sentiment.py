"""Apply the project's rating and sentiment filters to Apple App Store reviews."""
import json
import sys
from pathlib import Path

import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vendor" / "LeIA"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import OUTPUT  # noqa: E402


def main():
    if not OUTPUT["apple_reviews"].exists():
        raise SystemExit("Rode primeiro src/10_scrape_app_store_reviews.py.")
    try:
        from leia import SentimentIntensityAnalyzer as LeIAAnalyzer
    except ImportError as exc:
        raise RuntimeError("Clone o LeIA em vendor/LeIA conforme o README.") from exc

    frame = pd.read_csv(OUTPUT["apple_reviews"], encoding="utf-8-sig")
    scored = frame[pd.to_numeric(frame["score"], errors="coerce") <= 3].copy()
    vader, leia = SentimentIntensityAnalyzer(), LeIAAnalyzer()
    scored["compound"] = [
        leia.polarity_scores(str(text))["compound"]
        if str(lang).casefold().startswith("pt")
        else vader.polarity_scores(str(text))["compound"]
        for text, lang in zip(scored["content"], scored["lang"])
    ]
    critical = scored[scored["compound"] <= 0.05].copy()
    OUTPUT["apple_critical"].parent.mkdir(parents=True, exist_ok=True)
    critical.to_csv(OUTPUT["apple_critical"], index=False, encoding="utf-8-sig")
    metrics_path = OUTPUT["metrics"]
    try:
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        metrics = {}
    metrics["app_store_reviews"] = {
        "total": int(len(frame)),
        "rating_at_most_3": int(len(scored)),
        "critical_after_sentiment": int(len(critical)),
        "source_limit": "Brazilian public RSS feed; up to 10 pages per app; not a complete review archive",
    }
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Apple reviews: {len(frame)} total; {len(scored)} with score <= 3; {len(critical)} critical after sentiment.")
    print(f"Saved: {OUTPUT['apple_critical']}")


if __name__ == "__main__":
    main()
