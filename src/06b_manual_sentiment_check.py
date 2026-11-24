"""Etapa 6b — Checagem manual de 100 avaliações da Etapa 2 (sentimento e filtro).

Gera uma planilha única, estratificada por idioma (pt, en, es) e por grupo
(50 retidas como críticas + 50 removidas por sentimento positivo apesar de nota <= 3;
seed = C.SEED = 42), a partir das amostras já produzidas pelo src/06_filter_sentiment.py.

Após o preenchimento humano da coluna `e_critica_de_fato (s/n)`, calcula a taxa de erro
geral, falsos positivos, falsos negativos e o detalhamento por idioma/ferramenta e loja,
gravando o resultado em `outputs/funnel_metrics.json` (seção `06b_manual_sentiment_check`).

Uso:
  python src/06b_manual_sentiment_check.py --build   # gera data/checagem_manual_sentimento_100.csv
  python src/06b_manual_sentiment_check.py --score   # calcula a taxa de erro e atualiza outputs/
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
from rules import update_metrics, write_csv  # noqa: E402

SEED = getattr(C, "SEED", 42)
OUTPUT_SHEET = C.DATA / "checagem_manual_sentimento_100.csv"
ANSWER_COL = "e_critica_de_fato (s/n)"
OBS_COL = "observacao"

# Quotas por (idioma, grupo) somando 100 avaliações: 50 críticas + 50 removidas positivas.
QUOTAS = {
    ("pt", "critica"): 17,
    ("pt", "removida_positiva"): 17,
    ("en", "critica"): 17,
    ("en", "removida_positiva"): 16,
    ("es", "critica"): 16,
    ("es", "removida_positiva"): 17,
}

SOURCES = [
    ("br", "pt", "google_play", C.BRASIL / "google_play_store" / "reviews" / "checagem_manual_sentimento.csv"),
    ("br", "pt", "app_store", C.BRASIL / "app_store" / "reviews" / "checagem_manual_sentimento.csv"),
    ("us", "en", "google_play", C.market_dir("us") / "google_play_store" / "reviews" / "checagem_manual_sentimento.csv"),
    ("us", "en", "app_store", C.market_dir("us") / "app_store" / "reviews" / "checagem_manual_sentimento.csv"),
    ("es", "es", "google_play", C.market_dir("es") / "google_play_store" / "reviews" / "checagem_manual_sentimento.csv"),
    ("es", "es", "app_store", C.market_dir("es") / "app_store" / "reviews" / "checagem_manual_sentimento.csv"),
    ("mx", "es", "google_play", C.market_dir("mx") / "google_play_store" / "reviews" / "checagem_manual_sentimento.csv"),
    ("mx", "es", "app_store", C.market_dir("mx") / "app_store" / "reviews" / "checagem_manual_sentimento.csv"),
]


def load_source_samples(sources=None):
    frames = []
    for market, lang_group, store, path in (sources or SOURCES):
        if not path.exists():
            raise SystemExit(f"Arquivo de amostra ausente: {path}. Rode src/06_filter_sentiment.py antes.")
        df = pd.read_csv(path, encoding="utf-8-sig")
        df["market"] = market
        df["lang_group"] = lang_group
        df["store"] = store
        frames.append(df)
    pool = pd.concat(frames, ignore_index=True)
    # Evita duplicar textos idênticos compartilhados entre Espanha e México na Google Play.
    pool["_norm_text"] = pool["content"].fillna("").astype(str).str.lower().str.split().str.join(" ")
    pool = pool.drop_duplicates(subset=["lang_group", "store", "app_mask_id", "_norm_text"], keep="first")
    return pool.drop(columns=["_norm_text"])


def sample_stratified(pool, quotas=None, seed=SEED):
    """Seleciona amostra estratificada por (idioma, grupo), preservando ambas as lojas."""
    quotas = quotas or QUOTAS
    chosen = []
    for (lang_group, grupo), n_target in quotas.items():
        sub = pool[(pool.lang_group == lang_group) & (pool.grupo == grupo)]
        if len(sub) < n_target:
            raise SystemExit(f"Amostra insuficiente para ({lang_group}, {grupo}): {len(sub)} < {n_target}")
        # Garante representatividade de Google Play e App Store dentro do estrato.
        as_sub = sub[sub.store == "app_store"]
        gp_sub = sub[sub.store == "google_play"]
        n_as = min(len(as_sub), max(3, round(n_target * 0.3))) if len(as_sub) else 0
        n_gp = min(len(gp_sub), n_target - n_as)
        if n_gp + n_as < n_target:
            n_as = min(len(as_sub), n_target - n_gp)
        parts = []
        if n_gp:
            parts.append(gp_sub.sample(n_gp, random_state=seed))
        if n_as:
            parts.append(as_sub.sample(n_as, random_state=seed))
        chosen.append(pd.concat(parts, ignore_index=True))
    out = pd.concat(chosen, ignore_index=True)
    # Embaralha a ordem de apresentação mantendo reprodutibilidade pela semente.
    out = out.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    out.insert(0, "amostra_id", [f"M{i:03d}" for i in range(1, len(out) + 1)])
    cols = [
        "amostra_id", "market", "store", "lang_group", "grupo", "app_mask_id",
        "score", "sentiment", "compound", "content", ANSWER_COL, OBS_COL,
    ]
    out[ANSWER_COL] = ""
    out[OBS_COL] = ""
    return out[cols]


def _normalize_answer(val):
    s = "" if pd.isna(val) else str(val).strip().lower()
    if s in {"s", "sim", "y", "yes", "1"}:
        return "s"
    if s in {"n", "nao", "não", "no", "0"}:
        return "n"
    return ""


def compute_error_metrics(df):
    """Calcula taxa de erro geral, FP, FN e detalhamento por idioma e loja."""
    work = df.copy()
    work["ans"] = work[ANSWER_COL].map(_normalize_answer)
    missing = int((work["ans"] == "").sum())
    if missing:
        raise ValueError(f"Ainda faltam {missing} linha(s) sem resposta válida ('s' ou 'n') em {ANSWER_COL}.")

    # No grupo 'critica', o filtro manteve a avaliação -> erro (falso positivo) se ans == 'n'.
    # No grupo 'removida_positiva', o filtro descartou -> erro (falso negativo) se ans == 's'.
    work["is_error"] = ((work["grupo"] == "critica") & (work["ans"] == "n")) | (
        (work["grupo"] == "removida_positiva") & (work["ans"] == "s")
    )

    def summarize(frame):
        n = int(len(frame))
        err = int(frame["is_error"].sum())
        return {"n": n, "errors": err, "error_rate_pct": round(100 * err / n, 2) if n else 0.0}

    crit = work[work["grupo"] == "critica"]
    rem = work[work["grupo"] == "removida_positiva"]
    return {
        "seed": SEED,
        "overall": summarize(work),
        "false_positives_in_critical": summarize(crit),
        "false_negatives_in_removed_positive": summarize(rem),
        "by_language": {lang: summarize(g) for lang, g in work.groupby("lang_group")},
        "by_store": {store: summarize(g) for store, g in work.groupby("store")},
    }


def main():
    if C.MARKET != "br":
        raise SystemExit("Rode este script sem MARKET (ou MARKET=br).")
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--build", action="store_true", help="gera data/checagem_manual_sentimento_100.csv")
    mode.add_argument("--score", action="store_true", help="calcula taxa de erro da planilha preenchida")
    ap.add_argument("--sheet", type=Path, default=OUTPUT_SHEET, help="caminho da planilha de checagem")
    args = ap.parse_args()

    if args.build:
        pool = load_source_samples()
        sheet = sample_stratified(pool)
        write_csv(sheet, args.sheet)
        counts = sheet.groupby(["lang_group", "grupo", "store"]).size().to_dict()
        print(f"Planilha gerada: {args.sheet} ({len(sheet)} avaliações; seed={SEED})")
        print("Distribuição (idioma, grupo, loja):", counts)
        return

    if not args.sheet.exists():
        raise SystemExit(f"Planilha não encontrada: {args.sheet}. Rode com --build primeiro.")
    df = pd.read_csv(args.sheet, encoding="utf-8-sig")
    try:
        metrics = compute_error_metrics(df)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    update_metrics("06b_manual_sentiment_check", metrics)
    ov = metrics["overall"]
    fp = metrics["false_positives_in_critical"]
    fn = metrics["false_negatives_in_removed_positive"]
    print(f"Checagem concluída: {ov['errors']}/{ov['n']} erros ({ov['error_rate_pct']}%)")
    print(f"  - Falsos positivos entre críticas: {fp['errors']}/{fp['n']} ({fp['error_rate_pct']}%)")
    print(f"  - Falsos negativos entre removidas positivas: {fn['errors']}/{fn['n']} ({fn['error_rate_pct']}%)")
    print("  - Por idioma:", metrics["by_language"])
    print("  - Por loja:", metrics["by_store"])


if __name__ == "__main__":
    main()
