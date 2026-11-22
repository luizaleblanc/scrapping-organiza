"""Etapa 8b — Versão PÚBLICA das críticas dos mercados internacionais (EUA, Espanha, México).

Gera data/publico/mercados_internacionais/ sem nenhum identificador de app nem de avaliador:
  <país>/reviews_criticas.csv     app_mask_id, loja, score, content, lang, at, compound
  apps_em_varios_paises.csv       só máscara, países e quantidade de críticas (sem nome)
Fonte: as cópias redigidas do passo 7 (dados pessoais e QUALQUER nome de pessoa já trocados
por marcadores, data sem hora). Antes de gravar, confere que não sobrou e-mail, URL, @,
telefone/CPF nem data com hora; se sobrar, para sem gravar.
Não mexe nos arquivos públicos do Brasil (passo 8). Rode sem MARKET.
"""
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
from rules import update_metrics, write_csv  # noqa: E402

OUT = C.DATA / "publico" / "mercados_internacionais"
COLS = ["app_mask_id", "loja", "score", "content", "lang", "at", "compound"]
LEAKS = {
    "email": r"[\w.+-]+@[\w-]+\.[\w.]+",
    "url": r"https?://|www\.",
    "handle": r"(?<![\w\[])@\w{2,}",
    "cpf_ou_telefone": r"(?<!\d)\d{3}\.?\d{3}\.?\d{3}-?\d{2}(?!\d)|(?<!\d)\(?\d{2}\)?\s?9?\d{4}-\d{4}(?!\d)",
}


def check(df, where):
    text = df.content.fillna("").astype(str)
    for kind, pat in LEAKS.items():
        n = int(text.str.contains(pat, regex=True).sum())
        if n:
            raise SystemExit(f"{where}: {n} linha(s) com possível {kind}. Nada foi gravado; revise a redação.")
    if df["at"].astype(str).str.len().max() > 10:
        raise SystemExit(f"{where}: data com hora. Nada foi gravado; rode o passo 7 de novo.")


def main():
    if C.MARKET != "br":
        raise SystemExit("Rode este script sem MARKET (ou MARKET=br).")
    stats, frames = {}, {}
    for m, pais in C.MARKET_FOLDERS.items():
        base = C.market_dir(m)
        parts = []
        for loja, store in [("google_play", "google_play_store"), ("app_store", "app_store")]:
            p = base / store / "reviews_para_ia" / "reviews_critical_redacted.csv"
            if p.exists():
                parts.append(pd.read_csv(p, encoding="utf-8-sig", dtype={"at": str}).assign(loja=loja))
        if not parts:
            print(f"[{pais}] sem críticas redigidas (passos 5 a 7); pulando")
            continue
        df = pd.concat(parts, ignore_index=True)
        df = df[[c for c in COLS if c in df]].sort_values(["app_mask_id", "loja", "at"])
        check(df, pais)
        frames[pais] = df
    for pais, df in frames.items():  # só grava depois que TODOS os países passaram na checagem
        write_csv(df, OUT / pais / "reviews_criticas.csv")
        stats[pais] = {"criticas": int(len(df)), "apps": int(df.app_mask_id.nunique())}
        print(f"[{pais}] {len(df)} críticas de {df.app_mask_id.nunique()} apps -> {OUT / pais}")
    shared = C.DATA / "mercados_internacionais" / "apps_em_varios_paises.csv"
    if shared.exists():
        s = pd.read_csv(shared, encoding="utf-8-sig").drop(columns=["app"])  # sem nome do app
        write_csv(s, OUT / "apps_em_varios_paises.csv")
    update_metrics("08b_publico_internacional", stats)


if __name__ == "__main__":
    main()
