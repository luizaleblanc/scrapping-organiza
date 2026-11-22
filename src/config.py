"""Configuração única do pipeline (strings, regras de exclusão auditáveis e caminhos)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# Strings de busca aprovadas pela pesquisadora. Usadas nas DUAS lojas.
# Nenhuma outra string, nome de marca ou lista de candidatos é usada.
# ---------------------------------------------------------------------------
SEARCH_STRINGS = {
    "S1": "finanças",
    "S2": "organizador de finanças",
    "S3": "educador de finanças",
    "S4": "aplicativos financeiros",
    "S5": "ia para finanças",
    "S6": "organizador financeiro com ia",
}
LANG, COUNTRY = "pt", "br"
RESULTS_PER_TERM = 30
RECENCY_MONTHS = 12
REQUEST_DELAY_SECONDS = 1.0
APP_STORE_DELAY_SECONDS = 3.2  # Apple documenta ~20 buscas/minuto.

# ---------------------------------------------------------------------------
# Critérios de inclusão (artigo, seção 3.1)
# ---------------------------------------------------------------------------
FINANCE_CATEGORIES = {"finance", "financas"}  # critério 2 (texto normalizado)
# Educação financeira: categoria Educação é aceita SÓ quando título ou desenvolvedor
# indicam educação financeira (descrição não basta) (decisão da pesquisadora, 2026-11-22).
EDUCATION_CATEGORIES = {"education", "educacao"}
FINANCIAL_EDUCATION_TERMS = [
    "educacao financeira", "educador financeiro", "educadora financeira",
    "financial education", "financial literacy", "financas pessoais",
    "aprenda a investir", "aprender a investir", "inteligencia financeira",
    "curso de financas", "curso de educacao financeira", "organizar suas financas",
]
EXCLUDE_EDUCATION_OUT_OF_SCOPE = ["certificacao", "certificacoes", "simulado", "simulados", "cpa 10",
                                  "cpa 20", "cea", "ancord", "concurso", "trading", "trader"]
PRODUCTIVITY_GAME_CATEGORIES = {"productivity", "produtividade", "games", "jogos"}

# Termos comparados por palavra inteira no título + desenvolvedor normalizados.
EXCLUDE_CONFLICT_OF_INTEREST = ["organiza ai"]
EXCLUDE_PRODUCTIVITY_GAMES = [
    "trello", "notion", "todoist", "asana", "clickup", "evernote", "monday com",
    "google planilhas", "google sheets", "tycoon", "simulator", "simulador", "jogo", "game",
]
EXCLUDE_BANKS = [
    "nubank", "itau", "bradesco", "santander", "banco do brasil", "caixa", "banco inter",
    "inter co", "c6 bank", "btg", "banco neon", "neon pagamentos", "banco next", "crefisa",
    "sofi", "seabank", "honda servicos financeiros", "servicos financeiros",
    "financiamento", "financiamentos", "powpay", "cartao pre pago", "chase", "bank of america", "wells fargo", "capital one", "revolut", "monzo",
    "barclays", "ally bank", "us bank", "sicoob", "sicredi", "banrisul",
    "bank", "banco", "banking", "credit union", "conta digital", "conta pj", "banco digital",
    # maquininhas / adquirentes / instituições de pagamento
    "maquininha", "maquininhas", "maquina de cartao", "ton", "stone", "cielo", "getnet",
    "sumup", "infinitepay", "pagar me", "rede", "instituicao de pagamento",
    "instituicao de pagamentos",
]
EXCLUDE_WALLETS_PAYMENTS = [
    "picpay", "mercado pago", "pagbank", "pagseguro", "recargapay", "paypal", "venmo",
    "cash app", "zelle", "klarna", "wise", "afterpay", "affirm", "remitly", "western union",
    "send money", "money transfer",
    "e wallet", "ewallet", "digital wallet", "carteira digital", "envio de dinheiro",
    "taptap send", "isaac", "formatura", "carteira do google", "google wallet",
]
# Termos genéricos de pagamento: checados SÓ no título (no desenvolvedor geravam falso
# positivo, ex.: "OINC PAGAMENTOS E FINANCAS LTDA", app de orçamento pessoal).
EXCLUDE_PAYMENT_TITLE_ONLY = ["pix", "pagamento", "pagamentos", "payment", "payments"]
EXCLUDE_TRADING_CRYPTO = [
    "xp investimentos", "rico investimentos", "clear corretora", "toro investimentos",
    "binance", "coinbase", "robinhood", "webull", "metamask", "tradingview", "etoro",
    "crypto", "cripto", "criptomoeda", "criptomoedas", "bitcoin", "btc", "blockchain",
    "stock", "stocks", "acoes", "bolsa de valores", "trading", "trade", "trader", "day trade",
    "brokerage", "corretora", "investimento", "investimentos", "investment", "investing",
    "investidor", "investidor10", "metatrader", "metaquotes", "yahoo financas",
    "yahoo finance", "nelogica", "research", "dolar", "forex", "cambio",
    "consorcio", "consorcios",
]
EXCLUDE_B2B_CREDIT = [
    "quickbooks", "expensify", "expense report", "conta azul", "omie", "bling", "xero",
    "serasa", "boa vista", "credit karma", "credit score", "emprestimo", "emprestimos",
    "loan", "loans", "consignado", "fgts", "credito", "crediario", "cpf",
    "antecipacao de salario", "invoice", "invoicing", "nota fiscal", "nf e",
    "payroll", "gestao de vendas", "cobrancas", "for business", "empresarial",
]
# Sinais fortes na DESCRIÇÃO oficial (bancos/maquininhas/corretoras que não se
# denunciam pelo título). Termos amplos como "investimentos" ficam de fora porque
# apps de orçamento costumam citá-los.
EXCLUDE_DESCRIPTION = [
    "conta digital", "abra sua conta", "abertura de conta", "abrir sua conta",
    "maquininha", "instituicao de pagamento", "plataforma de trading", "negocie criptomoedas", "compre e venda criptomoedas",
]

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------
DATA = ROOT / "data"
GP_STORE = DATA / "google_play_store"
AS_STORE = DATA / "app_store"
GP_DIR = GP_STORE / "busca_e_triagem"
AS_DIR = AS_STORE / "busca_e_triagem"
CROSS_DIR = DATA / "apps_nas_duas_lojas"
PRIVATE_DIR = DATA / "chave_apps_mascarados_NAO_COMPARTILHAR"
OUTPUTS = ROOT / "outputs"
LOGS = ROOT / "logs"

PATHS = {
    "gp_hits": GP_DIR / "search_hits.csv",
    "gp_eligible": GP_DIR / "apps_eligible.csv",
    "gp_excluded": GP_DIR / "apps_excluded_audit.csv",
    "as_hits": AS_DIR / "search_hits.csv",
    "as_eligible": AS_DIR / "apps_eligible.csv",
    "as_excluded": AS_DIR / "apps_excluded_audit.csv",
    "both_stores": CROSS_DIR / "apps_both_stores.csv",
    "single_store": CROSS_DIR / "apps_single_store_excluded.csv",
    "manual_matches": CROSS_DIR / "manual_match_decisions.csv",
    "reviews": GP_STORE / "reviews/reviews_anonymized.csv",
    "critical": GP_STORE / "reviews/reviews_critical.csv",
    "as_reviews": AS_STORE / "reviews/reviews_anonymized.csv",
    "as_critical": AS_STORE / "reviews/reviews_critical.csv",
    "ai_full": GP_STORE / "reviews_para_ia/reviews_anonymized_redacted.csv",
    "ai_critical": GP_STORE / "reviews_para_ia/reviews_critical_redacted.csv",
    "ai_as_full": AS_STORE / "reviews_para_ia/reviews_anonymized_redacted.csv",
    "ai_as_critical": AS_STORE / "reviews_para_ia/reviews_critical_redacted.csv",
    "mapping": PRIVATE_DIR / "app_mapping.csv",
    "checkpoint": PRIVATE_DIR / "review_checkpoint.json",
    "metrics": OUTPUTS / "funnel_metrics.json",
    # Reviews do Google Play já coletadas em 2026-11-20 (reaproveitadas para não
    # repetir a raspagem dos mesmos apps).
    "legacy_reviews": ROOT / "arquivo_rodadas_anteriores/dados/pipeline_anterior_38_apps_strings_antigas/dados_processados/reviews_anonymized.csv",
    "legacy_mapping": ROOT / "arquivo_rodadas_anteriores/dados/pipeline_anterior_38_apps_strings_antigas/mapeamento_privado/app_mapping.csv",
}
