"""Compare full/critical review CSVs and create locally redacted AI-share copies."""
import json
import argparse
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from config import OUTPUT
from review_redaction import possible_number_counts, redact_text

REVIEW_KEY = ["app_mask_id", "content", "score", "lang", "at"]


def row_hashes(frame):
    """Build stable row fingerprints over the common review identity fields."""
    missing = [column for column in REVIEW_KEY if column not in frame.columns]
    if missing:
        raise ValueError(f"CSV is missing review columns: {', '.join(missing)}")
    keyed = frame[REVIEW_KEY].copy().fillna("")
    return pd.util.hash_pandas_object(keyed, index=False).astype("uint64")


def distribution(series):
    return {str(k): int(v) for k, v in series.fillna("NA").value_counts(dropna=False).items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply-to-source",
        action="store_true",
        help="substitui os CSVs de entrada pelas versões redigidas",
    )
    args = parser.parse_args()
    full_path = OUTPUT["reviews"]
    critical_path = OUTPUT["critical"]
    if not full_path.exists() or not critical_path.exists():
        raise SystemExit(
            "É preciso ter reviews_anonymized.csv e reviews_critical.csv antes da auditoria."
        )

    full = pd.read_csv(full_path, encoding="utf-8-sig")
    critical = pd.read_csv(critical_path, encoding="utf-8-sig")
    full_hashes = Counter(row_hashes(full).tolist())
    critical_hashes = Counter(row_hashes(critical).tolist())
    extra_hashes = critical_hashes - full_hashes
    common_hashes = full_hashes & critical_hashes
    missing_from_critical = sum(full_hashes.values()) - sum(common_hashes.values())

    score = pd.to_numeric(full["score"], errors="coerce")
    low_score_count = int((score <= 3).sum())
    compound = pd.to_numeric(critical.get("compound"), errors="coerce")
    content_full = full["content"].fillna("").astype(str)
    content_critical = critical["content"].fillna("").astype(str)
    uncertain_full = possible_number_counts(full["content"])
    uncertain_critical = possible_number_counts(critical["content"])

    output_dir = full_path.parent / "ai_share"
    output_dir.mkdir(parents=True, exist_ok=True)
    full_counters = Counter()
    critical_counters = Counter()
    full_redacted = full.copy()
    critical_redacted = critical.copy()
    full_redacted["content"] = [redact_text(x, full_counters) for x in content_full]
    critical_redacted["content"] = [redact_text(x, critical_counters) for x in content_critical]
    full_output = output_dir / "reviews_anonymized_redacted.csv"
    critical_output = output_dir / "reviews_critical_redacted.csv"
    full_redacted.to_csv(full_output, index=False, encoding="utf-8-sig")
    critical_redacted.to_csv(critical_output, index=False, encoding="utf-8-sig")

    if args.apply_to_source:
        full_temp = full_path.with_name(full_path.name + ".redacting.tmp")
        critical_temp = critical_path.with_name(critical_path.name + ".redacting.tmp")
        full_redacted.to_csv(full_temp, index=False, encoding="utf-8-sig")
        critical_redacted.to_csv(critical_temp, index=False, encoding="utf-8-sig")
        os.replace(full_temp, full_path)
        os.replace(critical_temp, critical_path)

    audit = {
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "full_reviews": str(full_path),
            "critical_reviews": str(critical_path),
        },
        "outputs": {
            "full_redacted": str(full_output),
            "critical_redacted": str(critical_output),
            "source_csvs_updated": bool(args.apply_to_source),
        },
        "divergence": {
            "full_rows": int(len(full)),
            "critical_rows": int(len(critical)),
            "full_app_masks": int(full["app_mask_id"].nunique()),
            "critical_app_masks": int(critical["app_mask_id"].nunique()),
            "critical_rows_not_found_in_full_multiset": int(sum(extra_hashes.values())),
            "full_rows_absent_from_critical": int(missing_from_critical),
            "rows_with_score_at_most_3": low_score_count,
            "rows_removed_by_sentiment_after_star_filter": int(low_score_count - len(critical)),
            "full_languages": distribution(full["lang"]),
            "critical_languages": distribution(critical["lang"]),
            "full_scores": distribution(full["score"]),
            "critical_scores": distribution(critical["score"]),
            "full_empty_text_rows": int(content_full.str.strip().eq("").sum()),
            "critical_empty_text_rows": int(content_critical.str.strip().eq("").sum()),
            "critical_compound_above_0_05": int((compound > 0.05).sum()),
        },
        "redactions": {
            "full_reviews_replacements_by_type": dict(full_counters),
            "critical_reviews_replacements_by_type": dict(critical_counters),
            "possible_phone_or_number_matches_before_redaction": {
                "full_reviews": uncertain_full,
                "critical_reviews": uncertain_critical,
            },
            "method": "Regex-based replacement of likely emails, URLs, CPFs, @handles, strict phone formats, and ambiguous 8-11 digit number strings not next to common currency symbols or matching common numeric date formats. Ambiguous values may be false positives.",
        },
        "notice": "Regex redaction cannot find every personal detail. Ambiguous number strings are replaced and may include non-personal values. Review the CSVs before external sharing.",
    }
    audit_path = OUTPUT["metrics"].parent / "review_csv_audit.json"
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Auditoria salva: {audit_path}")
    print(f"Cópias redigidas salvas em: {output_dir}")
    if args.apply_to_source:
        print("CSV de pesquisa atualizado com conteúdo redigido.")
    print(
        f"Linhas: base={len(full)}, críticas={len(critical)}; "
        f"críticas fora da base={sum(extra_hashes.values())}; "
        f"subconjunto após estrelas={low_score_count}; "
        f"removidas por sentimento={low_score_count - len(critical)}"
    )
    print(
        "Substituições de texto: "
        f"base={sum(full_counters.values())}, críticas={sum(critical_counters.values())}"
    )


if __name__ == "__main__":
    main()
