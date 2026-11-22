"""Etapa 5b — Coleta avaliações da App Store (Brasil) dos MESMOS apps da amostra.

Mudança de protocolo (decisão da pesquisadora, 2026-11-22): a App Store passa a ser
fonte de avaliações, além de busca/triagem.

Fonte: feed RSS público de avaliações da Apple (itunes.apple.com/br/rss/customerreviews),
ordenado por mais recentes. Limite do próprio feed: 10 páginas x 50 = até 500 avaliações
por app. É uma amostra recente, não o histórico completo (diferente da Google Play).

Anonimização na ingestão (igual à Google Play): autor, link e id da avaliação são
descartados; ficam só app_mask_id (mesma máscara APP_xxx da Google Play), texto
redigido, nota, idioma e data. Título + corpo da avaliação viram um único texto.
Saída: data/app_store/reviews/reviews_anonymized.csv
"""
import sys
import time
from collections import Counter
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
from review_redaction import redact_text  # noqa: E402
from rules import update_metrics, write_csv  # noqa: E402

FEED = "https://itunes.apple.com/{country}/rss/customerreviews/page={page}/id={track_id}/sortby=mostrecent/json"
MAX_PAGES = 10
COLUMNS = ["app_mask_id", "content", "score", "lang", "at"]


def fetch_raw(url):
    """Uma resposta JSON válida (lista de entradas) ou None após 6 tentativas."""
    for attempt in range(6):
        try:
            r = requests.get(url, timeout=30)
            if r.status_code == 200 and r.text.lstrip().startswith("{"):
                entries = r.json().get("feed", {}).get("entry", [])
                return [entries] if isinstance(entries, dict) else entries
        except (requests.RequestException, ValueError):
            pass
        time.sleep(5 * (attempt + 1))
    return None


def fetch_page(track_id, page):
    """A Apple às vezes devolve página VÁLIDA e VAZIA no meio do feed (ex.: Mobills
    veio com 200 de 500). Por isso página vazia é refeita até 3 vezes antes de ser
    aceita como vazia. Retorna lista de avaliações ou None (falha persistente)."""
    url = FEED.format(country=C.COUNTRY, page=page, track_id=track_id)
    for attempt in range(4):
        entries = fetch_raw(url)
        if entries is None:
            return None
        reviews = [e for e in entries if "im:rating" in e]
        if reviews:
            return reviews
        time.sleep(4 * (attempt + 1))
    return []


def to_row(mask, e, counter):
    title = e.get("title", {}).get("label", "")
    body = e.get("content", {}).get("label", "")
    text = f"{title}. {body}" if title and body else (body or title)
    return {"app_mask_id": mask, "content": redact_text(text, counter),
            "score": int(e["im:rating"]["label"]), "lang": C.LANG,
            "at": e.get("updated", {}).get("label", "")}


def main():
    mapping = pd.read_csv(C.PATHS["mapping"], encoding="utf-8-sig")
    both = pd.read_csv(C.PATHS["both_stores"], encoding="utf-8-sig")
    apps = mapping.merge(both[["gp_app_id", "as_track_id", "as_title"]], left_on="appId", right_on="gp_app_id")
    counter, rows, incomplete = Counter(), [], []
    for app in apps.itertuples():
        got, empty_streak = 0, 0
        for page in range(1, MAX_PAGES + 1):
            reviews = fetch_page(int(app.as_track_id), page)
            if reviews is None:
                incomplete.append(f"{app.app_mask_id} p{page}")
                continue
            if not reviews:
                empty_streak += 1
                if empty_streak >= 2:  # duas páginas vazias seguidas = fim real
                    break
                continue
            empty_streak = 0
            rows.extend(to_row(app.app_mask_id, e, counter) for e in reviews)
            got += len(reviews)
            time.sleep(C.APP_STORE_DELAY_SECONDS)
        print(f"{app.app_mask_id} {app.as_title}: {got} avaliações nesta rodada", flush=True)

    new = pd.DataFrame(rows, columns=COLUMNS)
    # Rodar de novo só acrescenta: junta com o arquivo existente e remove duplicatas.
    path = C.PATHS["as_reviews"]
    old = pd.read_csv(path, encoding="utf-8-sig") if path.exists() else pd.DataFrame(columns=COLUMNS)
    old = old[old.app_mask_id.isin(set(apps.app_mask_id))]
    df = (pd.concat([old, new], ignore_index=True).astype({"score": int, "at": str})
          .drop_duplicates(subset=COLUMNS).sort_values(["app_mask_id", "at"]))
    write_csv(df, path)
    per_app = {k: int(v) for k, v in df.app_mask_id.value_counts().sort_index().items()}
    update_metrics("05b_app_store_reviews", {
        "source": "Apple RSS customerreviews (br, mostrecent, max 10 páginas x 50)",
        "apps": int(len(apps)), "reviews_total": int(len(df)),
        "reviews_by_app_mask": per_app, "redactions": dict(counter),
        "incomplete_pages_last_run": incomplete,
    })
    print(f"Total acumulado (sem duplicatas): {len(df)} avaliações -> {path}")
    print("Por app:", ", ".join(f"{k}={v}" for k, v in per_app.items()))
    if incomplete:
        print(f"ATENÇÃO: páginas que falharam (rode de novo): {incomplete}")


if __name__ == "__main__":
    main()
