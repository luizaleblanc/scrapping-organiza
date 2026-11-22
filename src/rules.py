"""Regras de elegibilidade compartilhadas pelas duas lojas e utilitários comuns."""
import json
from datetime import datetime, timezone

import pandas as pd

import config as C
from text_norm import has_term, norm

REASONS = [
    "conflict_of_interest_organiza_ai",
    "wrong_category_productivity_or_game",
    "wrong_category_other",
    "excluded_bank_or_card_machine",
    "excluded_wallet_payment",
    "excluded_trading_crypto_investment",
    "excluded_b2b_accounting_credit",
    "excluded_by_official_description",
    "no_ratings",
    "missing_update_date",
    "outdated_over_12_months",
]


def classify(title, developer, category, ratings, updated, description, cutoff):
    """Aplica os critérios em cascata. Retorna (motivo, nota); motivo '' = elegível."""
    t, text = norm(title), f"{norm(title)} {norm(developer)}"
    cat = norm(category)
    if has_term(text, C.EXCLUDE_CONFLICT_OF_INTEREST):
        return "conflict_of_interest_organiza_ai", "Organiza AI não integra a amostra"
    is_fin_edu = False
    if cat in C.EDUCATION_CATEGORIES:
        evidence = text  # título + desenvolvedor (descrição gerava falsos positivos: Nibble, Economisto)
        if has_term(evidence, C.FINANCIAL_EDUCATION_TERMS) and not has_term(text, C.EXCLUDE_EDUCATION_OUT_OF_SCOPE):
            is_fin_edu = True
    if cat not in C.FINANCE_CATEGORIES and not is_fin_edu:
        if cat in C.PRODUCTIVITY_GAME_CATEGORIES or has_term(t, C.EXCLUDE_PRODUCTIVITY_GAMES):
            return "wrong_category_productivity_or_game", f"Categoria '{category}' (critério 2)"
        return "wrong_category_other", f"Categoria '{category}' != Finance (critério 2)"
    for reason, terms in [
        ("excluded_bank_or_card_machine", C.EXCLUDE_BANKS),
        ("excluded_wallet_payment", C.EXCLUDE_WALLETS_PAYMENTS),
        ("excluded_wallet_payment", None),
        ("excluded_trading_crypto_investment", C.EXCLUDE_TRADING_CRYPTO),
        ("excluded_b2b_accounting_credit", C.EXCLUDE_B2B_CREDIT),
    ]:
        hit = has_term(t, C.EXCLUDE_PAYMENT_TITLE_ONLY) if terms is None else has_term(text, terms)
        if hit:
            return reason, f"Termo '{hit}' no título" + ("" if terms is None else "/desenvolvedor")
    hit = has_term(norm(description), C.EXCLUDE_DESCRIPTION)
    if hit:
        return "excluded_by_official_description", f"Descrição oficial contém '{hit}'"
    ratings = pd.to_numeric(ratings, errors="coerce")
    if pd.isna(ratings) or ratings <= 0:
        return "no_ratings", "Sem avaliações (critério 3)"
    if pd.isna(updated):
        return "missing_update_date", "Data de atualização ausente"
    if updated < cutoff:
        return "outdated_over_12_months", f"Atualizado em {updated.date()} (< {cutoff.date()}, critério 6)"
    return "", "Elegível (educação financeira, categoria Educação)" if is_fin_edu else "Elegível"


def update_metrics(section, values):
    path = C.PATHS["metrics"]
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        metrics = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        metrics = {}
    metrics[section] = values
    metrics["updated_at"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(frame, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding="utf-8-sig")
