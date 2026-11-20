"""Retain reviews with <=3 stars and non-positive/neutral sentiment."""
import json, sys
from pathlib import Path
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vendor" / "LeIA"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import OUTPUT


def portuguese_compound(text, analyzer):
    return analyzer.polarity_scores(str(text))["compound"]


def main():
    try:
        from leia import SentimentIntensityAnalyzer as LeIAAnalyzer
    except ImportError as exc:
        raise RuntimeError("Clone the LeIA source into vendor/LeIA (see README); its upstream repository is not pip-installable.") from exc
    if not OUTPUT["reviews"].exists():
        raise SystemExit("Arquivo de reviews não encontrado. Primeiro aprove manualmente os apps em apps_screening.csv e execute src/03_scrape_reviews.py.")
    df = pd.read_csv(OUTPUT["reviews"])
    score_ok = pd.to_numeric(df["score"], errors="coerce") <= 3
    scored = df[score_ok].copy()
    vader = SentimentIntensityAnalyzer()
    leia = LeIAAnalyzer()
    scored["compound"] = [portuguese_compound(x, leia) if str(lang).startswith("pt") else vader.polarity_scores(str(x))["compound"] for x, lang in zip(scored["content"], scored["lang"])]
    critical = scored[scored["compound"] <= 0.05].copy()
    critical.to_csv(OUTPUT["critical"], index=False, encoding="utf-8-sig")
    metrics = json.loads(OUTPUT["metrics"].read_text(encoding="utf-8")) if OUTPUT["metrics"].exists() else {}
    metrics.update({"reviews_total": len(df), "removed_by_score": int(len(df)-len(scored)), "removed_by_sentiment": int(len(scored)-len(critical)), "final_by_language": critical.groupby("lang").size().to_dict()})
    OUTPUT["metrics"].write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__": main()


