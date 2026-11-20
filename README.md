# Google Play personal finance review pipeline

## Setup

Python 3.10+ recommended. Install dependencies with `python -m pip install -r requirements.txt`.

LeIA's upstream repository is source-only and has no `setup.py` or `pyproject.toml`, so install it by cloning the source into `vendor/LeIA`:

`git clone https://github.com/rafjaa/LeIA.git vendor/LeIA`

The sentiment script imports `leia.SentimentIntensityAnalyzer` from that source tree.

## Run

1. `python src/01_search_apps.py` searches the configured English/US and Portuguese/Brazil terms and writes deduplicated metadata to `data/raw/apps_candidates.csv`.
2. `python src/02_screen_apps.py` checks official category, review count, recent update, and likely Apple App Store availability using Apple's public search endpoint. Review criteria 1 (personal budgeting purpose) and 5 (B2C) in `data/processed/apps_screening.csv` and fill each decision with `yes` or `no` before continuing.
3. `python src/03_scrape_reviews.py` scrapes Google Play only for apps passing automatic checks and both manual decisions. Stored review fields are allowlisted; user names, photos, and review IDs are discarded in memory.
4. `python src/04_filter_sentiment.py` applies the star and language-specific sentiment filters.

Logs are timestamped in `logs/`; funnel counts are updated in `outputs/funnel_metrics.json`. The Apple query is an approximate cross-platform existence match and should be checked manually where ambiguous. Candidate metadata and screening contain app IDs/titles; the separate mapping in `data/private/` is created only when collection is explicitly run after manual screening.

## Search strategy

Google Play candidate searches use task-specific personal budgeting phrases in English and Portuguese. They exclude terms such as `educador de finanças` from the primary app sample because those searches bring financial education products that may not meet the budgeting-app inclusion criterion. Literature searches about review mining and scraping are separately recorded as `LITERATURE_SEARCH_QUERIES` in `src/config.py`; do not pass those queries to Google Play.

The current candidate CSV and screening CSV predate the latest query refinement. Rerun steps 1 and 2 to regenerate them.
