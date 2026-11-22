"""Audit App Store search results for financial-education apps only."""
import re
import shutil
import unicodedata
from pathlib import Path

import pandas as pd

from config import OUTPUT

USER_SEARCH_STRINGS = [
    "educação financeira",
]

EDUCATION_TITLE = re.compile(
    r"\b(educacao financeira|educador(?:a)? financeiro|financial education|finance education|"
    r"financial literacy|finance literacy|learn(?:ing)? about money|learn(?:ing)? finance|"
    r"curso de financas|aprender financas|educacao sobre dinheiro)\b"
)
BANK_OR_PAYMENT = re.compile(r"\b(bank|banco|banking|bancario|credit union|digital bank|banco digital|conta digital)\b")
BUSINESS_ONLY = re.compile(r"\b(payroll|invoice|invoicing|expense report|business expense|for business|corporate card)\b")
EXPLICIT_BANK_BRANDS = {
    "itau", "nubank", "santander", "bradesco", "banco do brasil", "caixa",
    "c6 bank", "btg pactual", "pagbank", "mercado pago", "picpay", "chase",
    "wells fargo", "bank of america", "capital one", "ally bank", "oneunited bank",
    "us bank", "revolut", "monzo", "barclays", "paypal", "venmo", "cash app",
}
EXACT_OUT_OF_SCOPE = {"trello", "trello rastreador de tarefas"}


def normalize(value):
    if pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKD", str(value))
    text = text.encode("ascii", "ignore").decode("ascii").casefold()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


ALLOWED_TERMS = [normalize(term) for term in USER_SEARCH_STRINGS]


def matched_user_terms(value):
    # The search provenance must be one of the four approved strings exactly.
    terms = [normalize(term) for term in str(value).split(";") if normalize(term)]
    return list(dict.fromkeys(term for term in terms if term in ALLOWED_TERMS))


def classify(row):
    title = str(row.get("trackName") or "")
    seller = str(row.get("artistName") or "")
    normalized_title = normalize(title)
    normalized_seller = normalize(seller)
    genre = str(row.get("primaryGenreName") or "")
    scope_terms = matched_user_terms(row.get("matched_terms", ""))

    if normalized_title in EXACT_OUT_OF_SCOPE or "trello" in normalized_title or "trello" in normalized_seller:
        return "exclude", "Trello/gerenciador de tarefas; fora do escopo de finanças pessoais", scope_terms

    bank_brand = any(brand in normalized_title or brand in normalized_seller for brand in EXPLICIT_BANK_BRANDS)
    if bank_brand or BANK_OR_PAYMENT.search(normalized_title) or BANK_OR_PAYMENT.search(normalized_seller):
        return "exclude", "Banco ou serviço bancário; fora do escopo de educação financeira", scope_terms

    if re.search(r"\b(trip|travel|viagem|viagem)\b", normalized_title) and re.search(r"\b(budget|orcamento)\b", normalized_title):
        return "exclude", "Orçamento exclusivo para viagens, fora do recorte de finanças pessoais gerais", scope_terms

    if genre.casefold() != "education":
        return "exclude", f"Categoria '{genre}' fora do escopo (somente Education)", scope_terms

    if not scope_terms:
        return "exclude", "Termo fora da única consulta aprovada", scope_terms

    if BUSINESS_ONLY.search(normalized_title) or str(genre).casefold() == "business":
        return "exclude", "Foco empresarial/operacional, fora do recorte de finanças pessoais B2C", scope_terms

    if EDUCATION_TITLE.search(normalized_title):
        return "include", "Categoria Education e título identificam educação financeira", scope_terms

    return "exclude", "Título não confirma conteúdo de educação financeira", scope_terms


def main():
    source_path = OUTPUT["apple_candidates_raw"]
    current_path = OUTPUT["apple_candidates"]
    if not source_path.exists():
        if not current_path.exists():
            raise SystemExit("Execute primeiro src/05_search_app_store.py para gerar os resultados brutos.")
        shutil.copy2(current_path, source_path)

    raw = pd.read_csv(source_path, encoding="utf-8-sig")
    decisions = raw.apply(classify, axis=1, result_type="expand")
    decisions.columns = ["audit_decision", "audit_reason", "audit_matched_user_terms"]
    audited = pd.concat([raw, decisions], axis=1)
    included = audited[audited["audit_decision"].eq("include")].copy()
    excluded_and_review = audited[~audited["audit_decision"].eq("include")].copy()

    audited_path = current_path.with_name("candidates_audited.csv")
    excluded_path = current_path.with_name("candidates_excluded.csv")
    current_path.parent.mkdir(parents=True, exist_ok=True)
    audited.to_csv(audited_path, index=False, encoding="utf-8-sig")
    included.drop(columns=["audit_decision", "audit_reason", "audit_matched_user_terms"]).to_csv(
        current_path, index=False, encoding="utf-8-sig"
    )
    excluded_and_review.to_csv(excluded_path, index=False, encoding="utf-8-sig")

    counts = audited["audit_decision"].value_counts().to_dict()
    bank_rows = audited[
        audited["audit_reason"].str.startswith("Banco ou serviço bancário")
    ]
    trello_rows = audited[
        audited["audit_reason"].str.startswith("Trello/")
    ]
    print(f"Candidatos brutos auditados: {len(raw)}")
    print(f"Incluídos: {counts.get('include', 0)}; revisão manual: {counts.get('manual_review', 0)}; excluídos: {counts.get('exclude', 0)}")
    print(f"Apps bancários excluídos: {len(bank_rows)}; Trello excluído: {len(trello_rows)}")
    print(f"Lista em escopo: {current_path}")
    print(f"Auditoria completa: {audited_path}")
    print(f"Excluídos + revisão manual: {excluded_path}")


if __name__ == "__main__":
    main()
