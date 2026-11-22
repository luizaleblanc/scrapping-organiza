"""Etapa 5 — Coleta reviews da Google Play SOMENTE dos apps presentes nas duas lojas.

- Nunca coleta reviews da App Store.
- Anonimização na ingestão: só app_mask_id, content (redigido), score, lang, at.
- Mascaramento APP_001... ; o mapeamento real fica em data/chave_apps_mascarados_NAO_COMPARTILHAR/app_mapping.csv.
- Reaproveita as reviews já coletadas em 2026-11-20 para apps que estavam na base
  antiga (use --no-reuse para coletar tudo de novo).
- Checkpoint por app: se cair, rode de novo e ele continua de onde parou.

Uso: python src/05_scrape_google_play_reviews.py [--no-reuse] [--max-per-app N]
"""
import argparse
import json
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


def legacy_reviews_by_app():
    """Reviews antigas indexadas pelo appId real (via mapeamento privado antigo)."""
    if not (C.PATHS["legacy_reviews"].exists() and C.PATHS["legacy_mapping"].exists()):
        return {}
    old_map = pd.read_csv(C.PATHS["legacy_mapping"], encoding="utf-8-sig")
    old = pd.read_csv(C.PATHS["legacy_reviews"], encoding="utf-8-sig")
    mask_to_app = dict(zip(old_map.app_mask_id, old_map.appId))
    old["appId"] = old.app_mask_id.map(mask_to_app)
    return {app: grp for app, grp in old.groupby("appId")}


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
    ap.add_argument("--no-reuse", action="store_true")
    ap.add_argument("--max-per-app", type=int, default=0, help="limite para testes (0 = todas)")
    args = ap.parse_args()

    both = pd.read_csv(C.PATHS["both_stores"], encoding="utf-8-sig").sort_values("gp_app_id")
    mapping = pd.DataFrame({"app_mask_id": [f"APP_{i:03d}" for i in range(1, len(both) + 1)],
                            "appId": both.gp_app_id.values, "title": both.gp_title.values})
    write_csv(mapping, C.PATHS["mapping"])

    ckpt_path = C.PATHS["checkpoint"]
    try:
        ckpt = json.loads(ckpt_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        ckpt = {}
    # checkpoint só vale para o mesmo conjunto de apps
    if ckpt.get("apps") != mapping.appId.tolist():
        ckpt = {"apps": mapping.appId.tolist(), "done": []}
    stored = (pd.read_csv(C.PATHS["reviews"], encoding="utf-8-sig")
              if ckpt["done"] and C.PATHS["reviews"].exists() else pd.DataFrame(columns=REVIEW_COLUMNS))
    legacy = {} if args.no_reuse else legacy_reviews_by_app()
    counter, source = Counter(), {}

    for row in mapping.itertuples():
        if row.appId in ckpt["done"]:
            continue
        if row.appId in legacy:
            got = legacy[row.appId].assign(app_mask_id=row.app_mask_id)[REVIEW_COLUMNS]
            got["content"] = [redact_text(x, counter) for x in got.content.fillna("")]
            source[row.appId] = "reused_2026-11-20"
        else:
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
