"""Configuração única do pipeline (strings, regras de exclusão auditáveis e caminhos)."""
import os
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

# ---------------------------------------------------------------------------
# Mercados extras (pedido do orientador, 22/11/2026): mesmas etapas 1 a 4 nas lojas
# em inglês (EUA) e espanhol (Espanha e México), com as 6 strings traduzidas.
# Escolha com a variável de ambiente MARKET (padrão "br" = protocolo original).
# ---------------------------------------------------------------------------
STRINGS_EN = {"S1": "finance", "S2": "finance organizer", "S3": "finance educator",
              "S4": "financial apps", "S5": "ai for finance", "S6": "ai financial organizer"}
STRINGS_ES = {"S1": "finanzas", "S2": "organizador de finanzas", "S3": "educador de finanzas",
              "S4": "aplicaciones financieras", "S5": "ia para finanzas",
              "S6": "organizador financiero con ia"}
MARKETS = {"br": ("pt", SEARCH_STRINGS), "us": ("en", STRINGS_EN),
           "es": ("es", STRINGS_ES), "mx": ("es", STRINGS_ES)}
EXTRA_MARKETS = ["us", "es", "mx"]
MARKET = os.environ.get("MARKET", "br").strip().lower()
if MARKET not in MARKETS:
    raise SystemExit(f"MARKET inválido: {MARKET!r}. Use um de {sorted(MARKETS)}")
if MARKET != "br":
    LANG, SEARCH_STRINGS = MARKETS[MARKET]
    COUNTRY = MARKET
HL, GL = f"{LANG}_{COUNTRY.upper()}", COUNTRY.upper()  # parâmetros da página web da Play Store
RESULTS_PER_TERM = 30
# Reviews críticas = nota <= 3 E sentimento NEGATIVO OU NEUTRO, como no artigo (seção 3):
# compound < 0,05 no VADER/LeIA (positivo começa em 0,05, corte padrão). Só as positivas
# são descartadas. No espanhol (pysentimiento): rótulo NEG ou NEU.
MAX_SCORE = 3
POSITIVE_COMPOUND = 0.05  # descarta compound >= 0,05
RECENCY_MONTHS = 12
REQUEST_DELAY_SECONDS = 1.0
APP_STORE_DELAY_SECONDS = 3.2  # Apple documenta ~20 buscas/minuto.

# ---------------------------------------------------------------------------
# Critérios de inclusão (artigo, seção 3.1)
# ---------------------------------------------------------------------------
FINANCE_CATEGORIES = {"finance", "financas", "finanzas"}  # critério 2 (texto normalizado)
# Educação financeira: categoria Educação é aceita SÓ quando título ou desenvolvedor
# indicam educação financeira (descrição não basta) (decisão da pesquisadora, 2026-11-22).
EDUCATION_CATEGORIES = {"education", "educacao", "educacion"}
FINANCIAL_EDUCATION_TERMS = [
    "educacao financeira", "educador financeiro", "educadora financeira",
    "financial education", "financial literacy", "financas pessoais",
    "aprenda a investir", "aprender a investir", "inteligencia financeira",
    "curso de financas", "curso de educacao financeira", "organizar suas financas",
]
EXCLUDE_EDUCATION_OUT_OF_SCOPE = ["certificacao", "certificacoes", "simulado", "simulados", "cpa 10",
                                  "cpa 20", "cea", "ancord", "concurso", "trading", "trader"]
PRODUCTIVITY_GAME_CATEGORIES = {"productivity", "produtividade", "productividad", "games", "jogos", "juegos"}

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

# Equivalentes em espanhol/inglês, aplicados SÓ fora do Brasil (a triagem original
# não muda). Mesma lógica das listas acima.
if MARKET != "br":
    FINANCIAL_EDUCATION_TERMS += ["educacion financiera", "finanzas personales", "personal finance",
                                  "money management", "aprende a invertir"]
    EXCLUDE_BANKS += ["cuenta digital", "abre tu cuenta", "terminal de pago", "card reader"]
    EXCLUDE_WALLETS_PAYMENTS += ["billetera", "billetera digital", "monedero", "envio de dinero",
                                 "enviar dinero", "transferencias"]
    EXCLUDE_PAYMENT_TITLE_ONLY += ["pago", "pagos"]
    EXCLUDE_TRADING_CRYPTO += ["inversion", "inversiones", "invertir", "criptomonedas", "bolsa",
                               "acciones", "divisas", "broker"]
    EXCLUDE_B2B_CREDIT += ["prestamo", "prestamos", "creditos", "factura", "facturacion",
                           "nomina", "para empresas", "credit repair"]
    # Marcas e termos que passaram na 1ª rodada (22/11/2026) e que no Brasil seriam excluídos
    EXCLUDE_BANKS += ["amex", "american express", "citi", "citi mobile", "discover", "hsbc", "banorte",
                      "bbva", "santander mexico", "banamex", "nequi", "simplii", "bread financial",
                      "fcu", "federal credit union", "ameriprise", "netspend", "prepaid", "prepago",
                      "tarjeta prepago", "debit card"]
    EXCLUDE_WALLETS_PAYMENTS += ["gopay", "intermex", "remittance", "remesas", "bayar", "qris"]
    EXCLUDE_TRADING_CRYPTO += ["invest", "invests", "invierte", "inversor", "wealth", "wealth manager",
                               "wealth management", "acorns", "fidelity", "fidelity investments",
                               "magnifi", "bitso", "gbm", "fintual", "finhabits", "yahoo finanzas",
                               "voya", "empower", "retirement", "jubilacion"]
    EXCLUDE_B2B_CREDIT += ["cred ai", "credit card", "cash advance", "instant cash", "fast cash", "credit", "financiate",
                           "financiera", "brigit", "dave", "klover", "possible finance",
                           "beyond finance", "debt relief", "prodigy finance", "sat movil", "cfe contigo"]
    EXCLUDE_DESCRIPTION += ["abre tu cuenta", "open an account", "open your account",
                            "trading platform", "buy and sell crypto"]

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------
DATA = ROOT / "data"
BRASIL = DATA / "brasil"  # tudo do Brasil fica separado dos mercados internacionais
GP_STORE = BRASIL / "google_play_store"
AS_STORE = BRASIL / "app_store"
GP_DIR = GP_STORE / "busca_e_triagem"
AS_DIR = AS_STORE / "busca_e_triagem"
CROSS_DIR = BRASIL / "apps_nas_duas_lojas"
# Higienização manual dos mercados internacionais (22/11/2026): apps que passaram nas
# regras por texto, mas que no Brasil seriam excluídos pelos mesmos critérios.
EXCLUDE_INTERNATIONAL_APPS = {
    "com.didiglobal.cashloan": "excluded_b2b_accounting_credit: empréstimo (DiDi Finanzas)",
    "com.efe.user": "excluded_trading_crypto_investment: consultoria de investimentos (Edelman Financial Engines)",
    "com.dolarapp": "excluded_trading_crypto_investment: conta em dólar e câmbio (ARQ/DolarApp)",
}
MARKET_FOLDERS = {"us": "estados_unidos", "es": "espanha", "mx": "mexico"}


def market_dir(m):
    """Pasta de um mercado internacional: data/mercados_internacionais/<país>/."""
    return DATA / "mercados_internacionais" / MARKET_FOLDERS[m]


BR_BOTH_STORES = CROSS_DIR / "apps_both_stores.csv"  # amostra original (sempre o Brasil)
MULTILANG_EXISTING = CROSS_DIR / "apps_both_stores_outros_idiomas.csv"
MULTILANG_NEW = CROSS_DIR / "apps_novos_outros_idiomas.csv"
MULTILANG_VALIDATED = CROSS_DIR / "apps_novos_outros_idiomas_validado.csv"
if MARKET != "br":  # cada mercado extra tem pastas próprias; os dados do Brasil não mudam
    _M = DATA / "mercados_internacionais" / MARKET_FOLDERS[MARKET]
    GP_STORE, AS_STORE = _M / "google_play_store", _M / "app_store"
    GP_DIR, AS_DIR = GP_STORE / "busca_e_triagem", AS_STORE / "busca_e_triagem"
    CROSS_DIR = _M / "apps_nas_duas_lojas"
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
    "checkpoint": PRIVATE_DIR / ("review_checkpoint.json" if MARKET == "br" else f"review_checkpoint_{MARKET}.json"),
    # Apps cuja coleta de reviews é feita: no Brasil, a amostra; nos mercados extras, as 40
    # apps com reviews naquele idioma + apps novos validados (gerado pelo 09b).
    "sample": CROSS_DIR / ("apps_both_stores.csv" if MARKET == "br" else "amostra_coleta.csv"),
    "metrics": OUTPUTS / ("funnel_metrics.json" if MARKET == "br" else f"funnel_metrics_{MARKET}.json"),
}
