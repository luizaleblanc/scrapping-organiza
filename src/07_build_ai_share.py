"""Etapa 7 — Gera as cópias redigidas para compartilhar com IA (data/<loja>/reviews_para_ia/).

Contém só app_mask_id, texto redigido, nota, idioma e data. Sem nomes de apps,
appIds ou dados de avaliadores. Confere que só apps da amostra (duas lojas) entram.
"""
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
from review_redaction import brand_regex, redact_brands, redact_person_names, redact_text  # noqa: E402
from rules import update_metrics, write_csv  # noqa: E402
from text_norm import brand  # noqa: E402


def app_brand_terms():
    """Marcas (nome-base do título e do desenvolvedor) de todos os apps de todas as amostras."""
    terms = set()
    for f in [C.BR_BOTH_STORES, *C.DATA.glob("mercados_internacionais/*/apps_nas_duas_lojas/apps_both_stores.csv")]:
        if f.exists():
            d = pd.read_csv(f, encoding="utf-8-sig")
            for col in ["gp_title", "as_title", "gp_developer", "as_developer"]:
                terms |= {brand(x) for x in d[col].dropna()}
    return terms


BRANDS = brand_regex(app_brand_terms())


def main():
    allowed = set(pd.read_csv(C.PATHS["mapping"], encoding="utf-8-sig").app_mask_id)
    counts = {}
    # Só as críticas: a cópia redigida de TODAS as reviews não era usada por nenhuma etapa.
    for src, dst in [("critical", "ai_critical"), ("as_critical", "ai_as_critical")]:
        if not C.PATHS[src].exists():
            print(f"{C.PATHS[src].name} não existe; pulando")
            continue
        df = pd.read_csv(C.PATHS[src], encoding="utf-8-sig")
        outside = set(df.app_mask_id) - allowed
        if outside:
            raise SystemExit(f"{src}: app_mask_id fora da amostra {sorted(outside)}; rode as etapas 4-6 de novo.")
        counter = Counter()
        df["content"] = [redact_text(x, counter) for x in df.content.fillna("").astype(str)]
        df["content"] = redact_brands(df.content.tolist(), BRANDS, counter)  # marcas da amostra -> [APP]
        df["content"] = redact_person_names(df.content.tolist(), counter)  # pessoas e outras marcas
        # Só a data (sem hora): o horário exato da review, junto com o texto, ajuda a
        # identificar quem escreveu.
        df["at"] = df["at"].astype(str).str.slice(0, 10)
        cols = ["app_mask_id", "content", "score", "lang", "at"] + (["compound"] if "compound" in df else [])
        write_csv(df[cols], C.PATHS[dst])
        counts[dst] = {"rows": int(len(df)), "apps": int(df.app_mask_id.nunique()), "redactions": dict(counter)}
        print(f"{C.PATHS[dst]}: {len(df)} linhas, {df.app_mask_id.nunique()} apps")
    update_metrics("07_ai_share", counts)


if __name__ == "__main__":
    main()
