"""Create aggregate, transparent behavioral-signal tags from redacted review text."""
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import OUTPUT  # noqa: E402

SIGNALS = {
    "expense_tracking": r"\b(lancar|registrar|anotar|despesa|gasto|categorizar)\w*\b",
    "budget_planning": r"\b(orcamento|planej\w*|limite de gasto|controle financeiro)\b",
    "savings_goals": r"\b(meta|economiz\w*|poup\w*|guardar dinheiro)\b",
    "automation_or_ai": r"\b(ia|inteligencia artificial|automatic\w*|open finance|sincron\w*)\b",
    "financial_insight": r"\b(relatorio|insight|dica|analise|entender|educa\w*)\b",
    "usage_routine": r"\b(rotina|habito|todo dia|diari\w*|mensal\w*|acompanhar)\b",
    "friction_or_abandonment": r"\b(desinstal\w*|cancelei|parei de usar|trav\w*|erro|nao funciona|falha)\b",
    "trust_or_privacy": r"\b(seguranca|privacidade|confi\w*|meus dados|vazamento)\b",
    "emotional_response": r"\b(ansiedad\w*|tranquil\w*|estress\w*|preocup\w*|alivi\w*)\b",
    "price_or_subscription": r"\b(preco|assinatura|caro|gratuito|gratuita|plano pago|cobranca)\b",
}


def normalize(text):
    text = unicodedata.normalize("NFKD", str(text or ""))
    return text.encode("ascii", "ignore").decode("ascii").casefold()


def main():
    if not OUTPUT["apple_reviews"].exists():
        raise SystemExit("Rode primeiro src/10_scrape_app_store_reviews.py.")
    reviews = pd.read_csv(OUTPUT["apple_reviews"], encoding="utf-8-sig").fillna("")
    critical = pd.read_csv(OUTPUT["apple_critical"], encoding="utf-8-sig").fillna("") if OUTPUT["apple_critical"].exists() else pd.DataFrame(columns=reviews.columns)
    patterns = {name: re.compile(pattern) for name, pattern in SIGNALS.items()}

    all_rows = []
    for cohort, frame in (("all_collected", reviews), ("critical", critical)):
        for row in frame.to_dict("records"):
            normalized = normalize(row.get("content", ""))
            tags = [name for name, pattern in patterns.items() if pattern.search(normalized)]
            all_rows.append({
                "app_mask_id": row.get("app_mask_id", ""),
                "cohort": cohort,
                "score": row.get("score", ""),
                "signal_tags": ";".join(tags),
            })
    coded = pd.DataFrame(all_rows, columns=["app_mask_id", "cohort", "score", "signal_tags"])
    OUTPUT["apple_behavior_codes"].parent.mkdir(parents=True, exist_ok=True)
    coded.to_csv(OUTPUT["apple_behavior_codes"], index=False, encoding="utf-8-sig")

    profiles = []
    app_ids = list(dict.fromkeys(reviews.get("app_mask_id", pd.Series(dtype=str)).astype(str).tolist()))
    for app_id in app_ids:
        entry = {"app_mask_id": app_id}
        for cohort in ("all_collected", "critical"):
            cohort_reviews = coded[(coded["app_mask_id"].astype(str) == app_id) & (coded["cohort"] == cohort)]
            entry[f"{cohort}_review_count"] = int(len(cohort_reviews))
            tagged = cohort_reviews[cohort_reviews["signal_tags"].astype(str).ne("")]
            entry[f"{cohort}_tagged_review_count"] = int(len(tagged))
            for signal in SIGNALS:
                count = int(tagged["signal_tags"].astype(str).str.split(";").apply(lambda tags: signal in tags).sum())
                entry[f"{cohort}_{signal}_count"] = count
                entry[f"{cohort}_{signal}_share"] = round(count / len(cohort_reviews), 4) if len(cohort_reviews) else 0.0
        profiles.append(entry)
    pd.DataFrame(profiles).to_csv(OUTPUT["apple_profile"], index=False, encoding="utf-8-sig")
    print(f"Codified {len(coded)} review rows; aggregate profiles for {len(profiles)} apps.")
    print("Signals are transparent keyword tags for self-reported review themes, not psychological profiles of individual users.")
    print(f"Coded rows: {OUTPUT['apple_behavior_codes']}")
    print(f"Aggregate profile: {OUTPUT['apple_profile']}")


if __name__ == "__main__":
    main()
