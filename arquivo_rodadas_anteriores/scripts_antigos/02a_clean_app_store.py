"""Higieniza a pasta app_store (critérios 1, 2, 3, 5 e 6) e deduplica internamente.

Entrada: candidatos brutos da App Store (somente leitura). A Apple é usada apenas para
busca/triagem; nenhum review da App Store é coletado aqui. A iTunes Lookup API só é
consultada para completar metadados ausentes de IDs já existentes.
Saídas: data/processed/app_store_clean.csv e data/processed/app_store_excluded_audit.csv.
"""
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
from text_norm import has_term, norm  # noqa: E402

LOOKUP_URL = "https://itunes.apple.com/lookup"
ESSENTIAL = ["primaryGenreName", "userRatingCount", "currentVersionReleaseDate"]
REASON_ORDER = [
    "conflict_of_interest_organiza_ai",
    "wrong_category_productivity_or_game",
    "wrong_category_other",
    "excluded_financial_type_bank",
    "excluded_financial_type_wallet_payment",
    "excluded_financial_type_brokerage_crypto",
    "excluded_b2b_accounting_credit",
    "no_ratings",
    "missing_update_date",
    "outdated_over_12_months",
]


def consolidate(raw, hits):
    """Deduplicação interna por trackId (fallback bundleId), agregando termos e regiões."""
    raw = raw.copy()
    raw["dedup_key"] = raw["trackId"].astype("Int64").astype(str)
    no_id = raw["trackId"].isna()
    raw.loc[no_id, "dedup_key"] = "bundle:" + raw.loc[no_id, "bundleId"].astype(str)
    hits = hits.copy()
    hits["dedup_key"] = hits["trackId"].astype("Int64").astype(str)
    agg = hits.groupby("dedup_key").agg(
        as_terms_found=("term_id", lambda s: ";".join(sorted(set(map(str, s))))),
        as_queries=("term", lambda s: ";".join(sorted(set(map(str, s))))),
        as_regions=("country", lambda s: ";".join(sorted(set(map(str, s))))),
        as_hit_count=("term", "size"),
    ).reset_index()
    before = len(raw)
    raw = raw.sort_values("best_rank").drop_duplicates("dedup_key", keep="first")
    out = raw.merge(agg, on="dedup_key", how="left")
    out["as_regions"] = out["as_regions"].fillna(out["matched_regions"])
    out["as_terms_found"] = out["as_terms_found"].fillna(out["matched_terms"])
    return out.reset_index(drop=True), before - len(out)


def lookup_missing(df):
    """Completa metadados ausentes via iTunes Lookup API oficial (IDs já existentes)."""
    df["metadata_enriched"] = False
    missing = df[df[ESSENTIAL].isna().any(axis=1) & df["trackId"].notna()]
    for idx, row in missing.iterrows():
        country = str(row.get("as_regions") or "br").split(";")[0]
        try:
            res = requests.get(LOOKUP_URL, params={"id": int(row.trackId), "country": country}, timeout=25)
            results = res.json().get("results", [])
        except (requests.RequestException, ValueError):
            results = []
        if results:
            for col in ESSENTIAL:
                if pd.isna(df.at[idx, col]):
                    df.at[idx, col] = results[0].get(col)
            df.at[idx, "metadata_enriched"] = True
        time.sleep(3.2)
    return df


def classify(row, cutoff):
    title, dev = norm(row.trackName), norm(row.artistName)
    text = f"{title} {dev}"
    genre = norm(row.primaryGenreName)

    if has_term(text, C.EXCLUDE_CONFLICT_OF_INTEREST):
        return "conflict_of_interest_organiza_ai", "Organiza AI não integra a amostra (seção 4.1)"
    if genre not in C.FINANCE_CATEGORIES:
        hit = has_term(title, C.EXCLUDE_PRODUCTIVITY_GAMES)
        if genre in {"games", "productivity"} or hit:
            extra = f"; termo '{hit}'" if hit else ""
            return "wrong_category_productivity_or_game", f"Categoria '{row.primaryGenreName}' != Finance{extra} (critério 2)"
        return "wrong_category_other", f"Categoria '{row.primaryGenreName}' != Finance (critério 2)"

    if True:  # sem exceções por lista de candidatos
        for reason, terms in [
            ("excluded_financial_type_bank", C.EXCLUDE_BANKS),
            ("excluded_financial_type_wallet_payment", C.EXCLUDE_WALLETS_PAYMENTS),
            ("excluded_financial_type_brokerage_crypto", C.EXCLUDE_BROKERAGE_CRYPTO),
            ("excluded_b2b_accounting_credit", C.EXCLUDE_B2B_CREDIT),
        ]:
            hit = has_term(text, terms)
            if hit:
                return reason, f"Termo '{hit}' em título/desenvolvedor (nota de rodapé 3 / critério 5)"

    ratings = pd.to_numeric(row.userRatingCount, errors="coerce")
    if pd.isna(ratings) or ratings <= 0:
        return "no_ratings", "Sem avaliações na App Store (critério 3)"
    updated = pd.to_datetime(row.currentVersionReleaseDate, utc=True, errors="coerce")
    if pd.isna(updated):
        return "missing_update_date", "Data de atualização ausente mesmo após Lookup API"
    if updated < cutoff:
        return "outdated_over_12_months", f"Última atualização {updated.date()} < corte {cutoff.date()} (critério 6)"
    return "", "Atende critérios 1, 2, 3, 5 e 6 na App Store"


def main():
    raw = pd.read_csv(C.APP_STORE_RAW_INPUT, encoding="utf-8-sig")
    hits = pd.read_csv(C.APP_STORE_HITS_INPUT, encoding="utf-8-sig")
    df, internal_dups = consolidate(raw, hits)
    df = lookup_missing(df)

    collected = pd.to_datetime(raw["collected_at"], utc=True, errors="coerce").max()
    cutoff = collected - timedelta(days=365)
    decisions = df.apply(lambda r: classify(r, cutoff), axis=1, result_type="expand")
    df["exclusion_reason"], df["audit_note"] = decisions[0], decisions[1]

    # Checagem final pela descrição oficial (somente apps que passaram nas regras de título).
    for idx in df.index[df.exclusion_reason.eq("")]:
        try:
            res = requests.get(LOOKUP_URL, params={"id": int(df.at[idx, "trackId"]), "country": "br"}, timeout=25)
            desc = norm((res.json().get("results") or [{}])[0].get("description", ""))
        except (requests.RequestException, ValueError):
            desc = ""
        hit = has_term(desc, C.EXCLUDE_BANK_DESCRIPTION)
        if hit:
            df.at[idx, "exclusion_reason"] = "excluded_financial_type_bank"
            df.at[idx, "audit_note"] = f"Descrição oficial contém '{hit}' (conta digital/banco)"
        time.sleep(3.2)

    clean = df[df.exclusion_reason.eq("")].drop(columns=["exclusion_reason"])
    excluded = df[df.exclusion_reason.ne("")]
    C.CLEAN_OUTPUT["as_clean"].parent.mkdir(parents=True, exist_ok=True)
    clean.to_csv(C.CLEAN_OUTPUT["as_clean"], index=False, encoding="utf-8-sig")
    excluded.to_csv(C.CLEAN_OUTPUT["as_excluded"], index=False, encoding="utf-8-sig")
    # Pasta data/raw/app_store: somente os elegíveis, colunas essenciais.
    eligible_cols = ["trackId", "bundleId", "trackName", "artistName", "primaryGenreName",
                     "averageUserRating", "userRatingCount", "currentVersionReleaseDate",
                     "trackViewUrl", "as_queries", "as_regions", "collected_at"]
    C.CLEAN_OUTPUT["as_eligible"].parent.mkdir(parents=True, exist_ok=True)
    clean[eligible_cols].sort_values("trackName").to_csv(
        C.CLEAN_OUTPUT["as_eligible"], index=False, encoding="utf-8-sig")

    counts = excluded.exclusion_reason.value_counts()
    stage = {
        "input_file": C.APP_STORE_RAW_INPUT.relative_to(C.ROOT).as_posix(),
        "app_store_raw_rows": int(len(raw)),
        "app_store_internal_duplicates_removed": int(internal_dups),
        "app_store_unique_after_dedup": int(len(df)),
        "metadata_enriched_via_lookup": int(df.metadata_enriched.sum()),
        "recency_cutoff_utc": cutoff.isoformat(),
        "removed_by_reason": {r: int(counts.get(r, 0)) for r in REASON_ORDER},
        "removed_total": int(len(excluded)),
        "app_store_clean": int(len(clean)),
        "approved_search_strings": C.APP_STORE_APPROVED_STRINGS,
        "hits_dropped_at_search_out_of_scope": int(len(pd.read_csv(C.APP_STORE_HITS_OUT_OF_SCOPE))),
    }
    path = C.CLEAN_OUTPUT["metrics"]
    metrics = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    metrics["generated_at"] = datetime.now(timezone.utc).isoformat()
    metrics["stage_02a_app_store_cleaning"] = stage
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(stage, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
