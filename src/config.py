"""Configuration for reproducible app discovery and review mining."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Google Play queries find apps to sample; broad education/finance and scraping
# terminology is kept out of this list to reduce banking and methodology noise.
SEARCH_TERMS = {
    "en": {"lang": "en", "country": "us", "terms": {"T1": "budget planner", "T2": "expense tracker", "T3": "personal finance", "T4": "AI money assistant", "T5": "money manager"}},
    "pt": {"lang": "pt", "country": "br", "terms": {"T1": "finanças pessoais", "T2": "organizador financeiro", "T3": "controle de gastos", "T4": "orçamento pessoal", "T5": "aplicativo de controle financeiro", "T6": "IA para finanças", "T7": "organizador financeiro com IA"}},
}
# Separate literature-search strings; these are not sent to Google Play.
LITERATURE_SEARCH_QUERIES = {
    "en": '("Google Play" OR "Android app reviews") AND ("user reviews" OR "app reviews") AND ("review mining" OR scraping OR "data collection")',
    "pt": '("Google Play" OR "loja de aplicativos") AND ("avaliações de aplicativos" OR "reviews de apps") AND ("mineração de avaliações" OR raspagem OR scraping)',
}
EXCLUDED_APP_NAME = "organiza ai"
RESULTS_PER_TERM = 30
RECENT_MONTHS = 12
REQUEST_DELAY_SECONDS = 1.0
MAX_RETRIES = 4
OUTPUT = {
    "candidates": ROOT / "data/raw/apps_candidates.csv",
    "screening": ROOT / "data/processed/apps_screening.csv",
    "mapping": ROOT / "data/private/app_mapping.csv",
    "reviews": ROOT / "data/processed/reviews_anonymized.csv",
    "critical": ROOT / "data/processed/reviews_critical.csv",
    "metrics": ROOT / "outputs/funnel_metrics.json",
    "logs": ROOT / "logs",
}

