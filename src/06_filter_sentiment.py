"""Etapa 6 — Pré-processamento + filtro de criticidade (guia, Etapas 1 e 2).

1. Pré-processamento (sobre todas as reviews coletadas):
   a. remove textos vazios;
   b. remove reviews com <= C.MIN_WORDS palavras (palavra = trecho separado por espaço);
   c. cria `content_clean` (minúsculas, espaços normalizados; sem stopwords nem stemming)
      e remove duplicatas exatas de `content_clean` dentro da loja (fica a mais antiga).
2. Sentimento (sobre o texto ORIGINAL, pois LeIA/VADER usam maiúsculas como intensificador):
   PT: LeIA; EN: VADER. compound >= 0,05 = positivo; <= -0,05 = negativo; entre = neutro.
   ES: pysentimiento (rótulo POS/NEU/NEG). compound = P(POS) - P(NEG), só referência.
3. Filtro (interseção): nota <= 3 E sentimento negativo ou neutro.
4. Amostras para checagem manual (seed C.SEED): 100 críticas + 100 removidas por sentimento positivo.

Outros idiomas: defina $env:MARKET (us, es, mx).
Saídas: reviews_critical.csv e checagem_manual_sentimento.csv na pasta de reviews de cada loja.
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

MIN_WORDS = getattr(C, "MIN_WORDS", 3)  # remove reviews com <= 3 palavras
SEED = getattr(C, "SEED", 42)
SAMPLE_N = 100
NEG_COMPOUND = -0.05


def spanish_analyzer():
    try:
        from pysentimiento import create_analyzer
    except ImportError as exc:
        raise SystemExit("Para espanhol instale: python -m pip install pysentimiento") from exc
    return create_analyzer(task="sentiment", lang="es")


def preprocess(df):
    """Retorna (df limpo, contagens de cada passo)."""
    steps = {"n0_collected": int(len(df))}
    text = df.content.fillna("").astype(str).str.strip()
    df = df[text != ""].copy()
    steps["removed_empty"] = steps["n0_collected"] - len(df)
    words = df.content.astype(str).str.split().str.len()
    before = len(df)
    df = df[words > MIN_WORDS].copy()
    steps["removed_short_le_3_words"] = before - len(df)
    df["content_clean"] = df.content.astype(str).str.lower().str.split().str.join(" ")
    before = len(df)
    df = df.sort_values("at").drop_duplicates(subset="content_clean", keep="first")
    steps["removed_exact_duplicates"] = before - len(df)
    steps["n1_after_preprocessing"] = int(len(df))
    return df, steps


def label_counts(labels):
    vc = labels.value_counts()
    total = int(vc.sum()) or 1
    return {k: {"n": int(vc.get(k, 0)), "pct": round(100 * vc.get(k, 0) / total, 2)} for k in ("pos", "neu", "neg")}


def main():
    try:
        from leia import SentimentIntensityAnalyzer as LeIA
    except ImportError as exc:
        raise SystemExit("LeIA não encontrado. Rode: git clone https://github.com/rafjaa/LeIA.git vendor/LeIA") from exc
    pt, en, es = LeIA(), SentimentIntensityAnalyzer(), None
    for store, src, dst in [("google_play", "reviews", "critical"), ("app_store", "as_reviews", "as_critical")]:
        if not C.PATHS[src].exists():
            print(f"[{store}] sem arquivo de reviews ({C.PATHS[src].name}); pulando")
            continue
        raw = pd.read_csv(C.PATHS[src], encoding="utf-8-sig")
        df, pre = preprocess(raw)

        is_es = df.lang.astype(str).str.startswith("es")
        df["compound"] = [None if str(lang).startswith("es") else
                          (pt if str(lang).startswith("pt") else en).polarity_scores(str(text))["compound"]
                          for text, lang in zip(df.content, df.lang)]
        comp = pd.to_numeric(df.compound)
        df["sentiment"] = None
        df.loc[comp.notna(), "sentiment"] = "neu"
        df.loc[comp >= C.POSITIVE_COMPOUND, "sentiment"] = "pos"  # 0,05 já é positivo
        df.loc[comp <= NEG_COMPOUND, "sentiment"] = "neg"
        if is_es.any():
            es = es or spanish_analyzer()
            preds = es.predict(df.loc[is_es, "content"].astype(str).tolist())
            df.loc[is_es, "compound"] = [p.probas["POS"] - p.probas["NEG"] for p in preds]
            df.loc[is_es, "sentiment"] = [p.output.lower() for p in preds]

        df["score"] = pd.to_numeric(df.score, errors="coerce")
        low = df[df.score <= C.MAX_SCORE]
        critical = low[low.sentiment.isin(["neg", "neu"])]
        removed_pos = low[low.sentiment == "pos"]
        write_csv(critical, C.PATHS[dst])

        sample = pd.concat([
            critical.sample(min(SAMPLE_N, len(critical)), random_state=SEED).assign(grupo="critica"),
            removed_pos.sample(min(SAMPLE_N, len(removed_pos)), random_state=SEED).assign(grupo="removida_positiva"),
        ])[["grupo", "app_mask_id", "score", "lang", "compound", "sentiment", "content"]]
        sample["e_critica_de_fato (s/n)"] = ""
        sample["observacao"] = ""
        write_csv(sample, C.PATHS[dst].parent / "checagem_manual_sentimento.csv")

        by_app = {app: label_counts(g.sentiment) for app, g in df.groupby("app_mask_id")}
        update_metrics(f"06_sentiment_{store}", {
            "preprocessing": pre,
            "sentiment_thresholds": {"pt_en": "compound >= 0,05 pos; <= -0,05 neg; entre = neu",
                                     "es": "rótulo pysentimiento"},
            "sentiment_distribution_all": label_counts(df.sentiment),
            "sentiment_distribution_by_app_mask": by_app,
            "filter_rule": "interseção: nota <= 3 E sentimento neg/neu",
            "stars_only_le_3": int(len(low)),
            "removed_by_score_gt_3": int(len(df) - len(low)),
            "removed_by_positive_sentiment": int(len(removed_pos)),
            "critical_reviews": int(len(critical)),
            "critical_by_app_mask": {k: int(v) for k, v in critical.app_mask_id.value_counts().sort_index().items()},
            "manual_check_sample": {"seed": SEED, "critical": min(SAMPLE_N, len(critical)),
                                    "removed_positive": min(SAMPLE_N, len(removed_pos))},
        })
        print(f"[{store}] {pre['n0_collected']} coletadas -> {pre['n1_after_preprocessing']} após pré-proc. "
              f"-> {len(low)} nota <= 3 -> {len(critical)} críticas")


if __name__ == "__main__":
    main()
