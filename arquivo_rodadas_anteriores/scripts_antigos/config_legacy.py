"""Configuration for reproducible app discovery and review mining."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Approved discovery query: financial education only.
SEARCH_TERMS = {
    "pt": {"lang": "pt", "country": "br", "terms": {
        "T1": "educação financeira",
    }},
}
# Separate literature-search strings; these are not sent to Google Play.
LITERATURE_SEARCH_QUERIES = {
    "en": '("Google Play" OR "Android app reviews") AND ("user reviews" OR "app reviews") AND ("review mining" OR scraping OR "data collection")',
    "pt": '("Google Play" OR "loja de aplicativos") AND ("avaliações de aplicativos" OR "reviews de apps") AND ("mineração de avaliações" OR raspagem OR scraping)',
}
EXCLUDED_APP_NAME = "organiza ai"
RESULTS_PER_TERM = 30
# App Store uses the same single financial-education query in Brazil.
APP_STORE_SEARCH_TERMS = {
    "pt": {"lang": "pt", "country": "br", "terms": {
        "S1": "educação financeira"}},
}
# No branded queries; discovery uses only the four approved strings.
APP_STORE_BRAND_QUERIES = []
RECENT_MONTHS = 12
REQUEST_DELAY_SECONDS = 1.0
APP_STORE_REQUEST_DELAY_SECONDS = 3.2  # Apple documents ~20 search calls/minute.
MAX_RETRIES = 4
OUTPUT = {
    "candidates": ROOT / "data/raw/apps_candidates.csv",
    "candidates_excluded": ROOT / "data/raw/apps_candidates_excluded.csv",
    "apple_candidates": ROOT / "data/raw/app_store/candidates.csv",
    "apple_candidates_raw": ROOT / "data/raw/app_store/candidates_raw.csv",
    "apple_hits": ROOT / "data/raw/app_store/search_hits.csv",
    "apple_hits_all": ROOT / "data/raw/app_store/search_hits_all.csv",
    "apple_hits_excluded": ROOT / "data/raw/app_store/search_hits_excluded.csv",
    "apple_reviews": ROOT / "data/processed/app_store_reviews.csv",
    "apple_critical": ROOT / "data/processed/app_store_reviews_critical.csv",
    "apple_mapping": ROOT / "data/private/app_store_review_mapping.csv",
    "apple_profile": ROOT / "outputs/app_store_behavioral_profile.csv",
    "apple_behavior_codes": ROOT / "data/processed/app_store_behavior_codes.csv",
    "screening": ROOT / "data/processed/apps_screening.csv",
    "mapping": ROOT / "data/private/app_mapping.csv",
    "reviews": ROOT / "data/processed/reviews_anonymized.csv",
    "critical": ROOT / "data/processed/reviews_critical.csv",
    "metrics": ROOT / "outputs/funnel_metrics.json",
    "logs": ROOT / "logs",
}


# ---------------------------------------------------------------------------
# Higienização App Store + deduplicação cruzada (src/02a, src/02b).
# Listas auditáveis: cada termo é comparado ao texto normalizado (sem acento,
# minúsculo) do título e do desenvolvedor, por palavra inteira.
# ---------------------------------------------------------------------------
# Strings de busca aprovadas pela pesquisadora (2026-11-22). NÃO usar outras.
APP_STORE_APPROVED_STRINGS = {
    "S1": "finanças",
    "S2": "organizador de finanças",
    "S3": "educador de finanças",
    "S4": "aplicativos financeiros",
    "S5": "ia para finanças",
    "S6": "organizador financeiro com ia",
}
APP_STORE_COUNTRY = "br"
APP_STORE_RESULTS_PER_TERM = 30
APP_STORE_RAW_INPUT = ROOT / "data/archive/app_store/approved_strings/apps_raw.csv"
APP_STORE_HITS_ALL = ROOT / "data/archive/app_store/approved_strings/search_hits_all.csv"
APP_STORE_HITS_INPUT = ROOT / "data/archive/app_store/approved_strings/search_hits.csv"
APP_STORE_HITS_OUT_OF_SCOPE = ROOT / "data/archive/app_store/approved_strings/search_hits_out_of_scope.csv"
GOOGLE_PLAY_INPUT = ROOT / "data/processed/previous_scope_20261120/apps_screening.csv"
AI_SHARE_MAPPING = ROOT / "data/private/app_mapping.csv"
CLEAN_OUTPUT = {
    "as_clean": ROOT / "data/processed/app_store_clean.csv",
    "as_eligible": ROOT / "data/raw/app_store/apps_eligible.csv",
    "as_excluded": ROOT / "data/processed/app_store_excluded_audit.csv",
    "cross": ROOT / "data/processed/apps_cross_platform_dedup.csv",
    "single": ROOT / "data/processed/apps_single_store_excluded.csv",
    "gp_excluded": ROOT / "data/processed/google_play_excluded_audit.csv",
    "metrics": ROOT / "outputs/app_store_cleaning_and_dedup_metrics.json",
}
FINANCE_CATEGORIES = {"finance", "financas"}
RECENCY_MONTHS = 12

# Critério 2: falsos positivos de produtividade/organização e jogos.
EXCLUDE_PRODUCTIVITY_GAMES = [
    "trello", "notion", "todoist", "asana", "clickup", "evernote", "monday com",
    "tycoon", "simulator", "simulador", "idle", "merge", "puzzle", "jogo", "game",
]
# Nota de rodapé 3: bancos.
EXCLUDE_BANKS = [
    "nubank", "itau", "bradesco", "santander", "banco do brasil", "caixa", "banco inter",
    "inter co", "c6 bank", "btg", "banco neon", "neon pagamentos", "banco next",
    "chase", "bank of america", "wells fargo", "capital one", "revolut", "monzo",
    "barclays", "ally bank", "us bank", "sicoob", "sicredi", "banrisul",
    "bank", "banco", "banking", "credit union", "conta digital", "conta pj", "banco digital",
    # maquininhas / adquirentes
    "maquininha", "maquininhas", "maquina de cartao", "ton", "stone", "cielo", "getnet",
    "sumup", "infinitepay", "pagar me", "rede", "instituicao de pagamento", "instituicao de pagamentos",
]
# Carteiras digitais, pagamentos, BNPL, remessas.
EXCLUDE_WALLETS_PAYMENTS = [
    "picpay", "mercado pago", "pagbank", "pagseguro", "recargapay", "paypal", "venmo",
    "cash app", "zelle", "klarna", "wise", "afterpay", "affirm", "remitly", "western union",
    "pix", "pagamento", "pagamentos", "payment", "payments", "send money", "money transfer",
    "e wallet", "ewallet", "digital wallet", "carteira digital",
    "envio de dinheiro", "taptap send", "isaac", "formatura",
]
# Corretoras, investimentos e cripto.
EXCLUDE_BROKERAGE_CRYPTO = [
    "xp investimentos", "rico investimentos", "clear corretora", "toro investimentos",
    "binance", "coinbase", "robinhood", "webull", "metamask", "tradingview", "etoro",
    "crypto", "cripto", "bitcoin", "blockchain", "stock", "stocks", "trading", "trade",
    "brokerage", "corretora", "investimento", "investimentos", "investment", "investing",
    "dolar", "forex", "investidor", "investidor10", "nelogica", "research",
    "assessor", "assessores", "consorcio", "consorcios",
]
# B2B / contábil / crédito, score e empréstimos.
EXCLUDE_B2B_CREDIT = [
    "quickbooks", "expensify", "expense report", "conta azul", "omie", "bling", "xero", "serasa", "boa vista",
    "credit karma", "credit score", "emprestimo", "emprestimos", "loan", "loans",
    "consignado", "fgts", "credito", "crediario", "cpf",
    "antecipacao de salario", "desenrola", "invoice", "invoicing", "nota fiscal", "nf e", "payroll",
    "gestao de vendas", "cobrancas", "for business", "empresarial",
]
EXCLUDE_CONFLICT_OF_INTEREST = ["organiza ai"]
# Sinais de banco/conta digital/maquininha na DESCRIÇÃO oficial (iTunes Lookup API).
EXCLUDE_BANK_DESCRIPTION = [
    "conta digital", "abra sua conta", "abertura de conta", "abrir sua conta",
    "maquininha", "instituicao de pagamento", "cartao de credito sem anuidade",
]
# Sem lista de candidatos: a amostra vem só das strings aprovadas.
