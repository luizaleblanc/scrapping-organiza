"""Etapa 5 — Coleta reviews da Google Play SOMENTE dos apps presentes nas duas lojas.

- Nunca coleta reviews da App Store.
- Anonimização na ingestão: só app_mask_id, content (redigido), score, lang, at.
- Mascaramento APP_001... ; o mapeamento real fica em data/chave_apps_mascarados_NAO_COMPARTILHAR/app_mapping.csv.
- Checkpoint por app: se cair, rode de novo e ele continua de onde parou.

Uso: python src/05_scrape_google_play_reviews.py [--max-per-app N]
"""
import argparse
import json
import secrets
import socket
import sys
import time
from collections import Counter
from pathlib import Path

import pandas as pd
from google_play_scraper import Sort, reviews

socket.setdefaulttimeout(30)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
from review_redaction import redact_text  # noqa: E402
from rules import update_metrics, write_csv  # noqa: E402

REVIEW_COLUMNS = ["app_mask_id", "content", "score", "lang", "at"]


def build_mapping(both):
    """Máscaras SORTEADAS (nunca em ordem alfabética, que permitiria reconstruir a
    chave a partir da lista de apps). Reaproveita a chave existente para os mesmos
    apps; apps novos recebem máscaras livres sorteadas."""
    old = (pd.read_csv(C.PATHS["mapping"], encoding="utf-8-sig") if C.PATHS["mapping"].exists()
           else pd.DataFrame(columns=["app_mask_id", "appId", "title"]))
    keep = old[old.appId.isin(set(both.gp_app_id))]
    new_apps = both[~both.gp_app_id.isin(set(keep.appId))]
    free = [f"APP_{i:03d}" for i in range(1, len(both) + len(old) + 1) if f"APP_{i:03d}" not in set(keep.app_mask_id)]
    secrets.SystemRandom().shuffle(free)
    added = pd.DataFrame({"app_mask_id": free[:len(new_apps)], "appId": new_apps.gp_app_id.values,
                          "title": new_apps.gp_title.values})
    return pd.concat([keep, added], ignore_index=True).sort_values("app_mask_id").reset_index(drop=True)


def scrape(app_id, mask, max_per_app, counter):
    out, token = [], None
    while True:
        for attempt in range(4):
            try:
                batch, token = reviews(app_id, lang=C.LANG, country=C.COUNTRY, sort=Sort.NEWEST,
                                       count=200, continuation_token=token)
                break
            except Exception:
                if attempt == 3:
                    raise
                time.sleep(2 ** (attempt + 1))
        for item in batch:  # allowlist: nome, foto e id do avaliador nunca são gravados
            out.append({"app_mask_id": mask, "content": redact_text(item.get("content", ""), counter),
                        "score": item.get("score"), "lang": C.LANG, "at": str(item.get("at", ""))})
        if len(out) // 2000 != (len(out) - len(batch)) // 2000:
            print(f"   {mask}: {len(out)} reviews coletadas até agora...", flush=True)
        if max_per_app and len(out) >= max_per_app:
            return out[:max_per_app]
        if not batch or getattr(token, "token", None) is None:
            return out
        time.sleep(C.REQUEST_DELAY_SECONDS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-reuse", action="store_true", help="mantido por compatibilidade; a coleta é sempre nova")
    ap.add_argument("--max-per-app", type=int, default=0, help="limite para testes (0 = todas)")
    args = ap.parse_args()

    both = pd.read_csv(C.PATHS["both_stores"], encoding="utf-8-sig").sort_values("gp_app_id")
    mapping = build_mapping(both)
    write_csv(mapping, C.PATHS["mapping"])

    ckpt_path = C.PATHS["checkpoint"]
    try:
        ckpt = json.loads(ckpt_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        ckpt = {}
    # checkpoint só vale para o mesmo conjunto de apps
    if sorted(ckpt.get("apps", [])) != sorted(mapping.appId.tolist()):
        ckpt = {"apps": mapping.appId.tolist(), "done": []}
    stored = (pd.read_csv(C.PATHS["reviews"], encoding="utf-8-sig")
              if ckpt["done"] and C.PATHS["reviews"].exists() else pd.DataFrame(columns=REVIEW_COLUMNS))
    counter, source = Counter(), {}

    for row in mapping.itertuples():
        if row.appId in ckpt["done"]:
            continue
        got = pd.DataFrame(scrape(row.appId, row.app_mask_id, args.max_per_app, counter), columns=REVIEW_COLUMNS)
        source[row.appId] = "scraped_now"
        print(f"{row.app_mask_id} {row.title}: {len(got)} reviews ({source[row.appId]})")
        stored = pd.concat([stored, got], ignore_index=True)
        write_csv(stored, C.PATHS["reviews"])
        ckpt["done"].append(row.appId)
        ckpt_path.write_text(json.dumps(ckpt, ensure_ascii=False, indent=2), encoding="utf-8")

    update_metrics("05_reviews", {
        "apps": int(len(mapping)), "reviews_total": int(len(stored)),
        "reviews_by_app_mask": {k: int(v) for k, v in stored.app_mask_id.value_counts().sort_index().items()},
        "source_by_app_this_run": source, "redactions_this_run": dict(counter),
        "max_per_app": args.max_per_app or "all",
    })
    print(f"Total: {len(stored)} reviews -> {C.PATHS['reviews']}")


if __name__ == "__main__":
    main()
