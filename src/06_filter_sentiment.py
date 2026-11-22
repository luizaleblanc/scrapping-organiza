"""Etapa 6 — Mantém reviews críticas: nota <= 3 e sentimento negativo/neutro.

PT: LeIA (vendor/LeIA); EN: VADER. Compound <= 0.05 conta como neutro/negativo.
Saídas: data/google_play_store/reviews/reviews_critical.csv e data/app_store/reviews/reviews_critical.csv
"""
import sys
from pathlib import Path

import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor" / "LeIA"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
from rules import update_metrics, write_csv  # noqa: E402


def main():
    try:
        from leia import SentimentIntensityAnalyzer as LeIA
    except ImportError as exc:
        raise SystemExit("LeIA não encontrado. Rode: git clone https://github.com/rafjaa/LeIA.git vendor/LeIA") from exc
    pt, en = LeIA(), SentimentIntensityAnalyzer()
    for store, src, dst in [("google_play", "reviews", "critical"), ("app_store", "as_reviews", "as_critical")]:
        if not C.PATHS[src].exists():
            print(f"[{store}] sem arquivo de reviews ({C.PATHS[src].name}); pulando")
            continue
        df = pd.read_csv(C.PATHS[src], encoding="utf-8-sig")
        low = df[pd.to_numeric(df.score, errors="coerce") <= 3].copy()
        low["compound"] = [(pt if str(lang).startswith("pt") else en).polarity_scores(str(text))["compound"]
                           for text, lang in zip(low.content, low.lang)]
        critical = low[low.compound <= 0.05]
        write_csv(critical, C.PATHS[dst])
        update_metrics(f"06_sentiment_{store}", {
            "reviews_total": int(len(df)), "removed_by_score_gt_3": int(len(df) - len(low)),
            "removed_by_positive_sentiment": int(len(low) - len(critical)),
            "critical_reviews": int(len(critical)),
            "critical_by_app_mask": {k: int(v) for k, v in critical.app_mask_id.value_counts().sort_index().items()},
        })
        print(f"[{store}] {len(df)} reviews -> {len(low)} com nota <= 3 -> {len(critical)} críticas -> {C.PATHS[dst]}")

if __name__ == "__main__":
    main()
