"""Etapa 8b — Críticas PÚBLICAS de todos os países, em tabelas pequenas para ler no GitHub.

data/publico/<país>/apps.csv            apps do país só com máscara, categoria e nº de críticas
data/publico/<país>/<loja>/APP_xxx.csv  (ou APP_xxx_parte1.csv, _parte2... acima de 1.500 linhas)
  país: brasil, estados_unidos, espanha, mexico   loja: google_play, app_store
  colunas: app_mask_id, score, content, lang, at, compound
data/publico/mercados_internacionais/apps_em_varios_paises.csv  (só máscara, sem nome de app)

O GitHub só mostra um CSV como tabela se ele for pequeno (~512 KB); por isso a divisão.
Fonte: as cópias redigidas do passo 7: dados pessoais, nomes de pessoas ([NOME]), marcas dos
apps ([APP]), outras marcas ([MARCA]) e lugares ([LOCAL]) trocados por marcadores; data sem
hora. Antes de gravar, confere que não sobrou marca de app, e-mail, URL, @, telefone/CPF nem
data com hora; se sobrar, para sem gravar nada. Rode sem MARKET.
Um país por vez: python src/08b_build_public_criticas.py --paises espanha
"""
import argparse
import importlib
import shutil
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
from rules import update_metrics, write_csv  # noqa: E402

PUB = C.DATA / "publico"
ROWS_PER_FILE = 1500
COLS = ["app_mask_id", "score", "content", "lang", "at", "compound"]
PAISES = {"br": "brasil", **C.MARKET_FOLDERS}
LEAKS = {
    "email": r"[\w.+-]+@[\w-]+\.[\w.]+",
    "url": r"https?://|www\.",
    "handle": r"(?<![\w\[])@\w{2,}",
    "cpf_ou_telefone": r"(?<!\d)\d{3}\.?\d{3}\.?\d{3}-?\d{2}(?!\d)|(?<!\d)\(?\d{2}\)?\s?9?\d{4}-\d{4}(?!\d)",
}


BRANDS = importlib.import_module("07_build_ai_share").BRANDS  # marcas da amostra


def check(df, where):
    text = df.content.fillna("").astype(str)
    n = int(text.map(lambda t: bool(BRANDS.search(t))).sum()) if BRANDS is not None else 0
    if n:
        raise SystemExit(f"{where}: {n} linha(s) ainda com marca de app. Nada foi gravado; rode o passo 7 de novo.")
    for kind, pat in LEAKS.items():
        n = int(text.str.contains(pat, regex=True).sum())
        if n:
            raise SystemExit(f"{where}: {n} linha(s) com possível {kind}. Nada foi gravado; revise a redação.")
    if df["at"].astype(str).str.len().max() > 10:
        raise SystemExit(f"{where}: data com hora. Nada foi gravado; rode o passo 7 de novo.")


def main():
    if C.MARKET != "br":
        raise SystemExit("Rode este script sem MARKET (ou MARKET=br).")
    ap = argparse.ArgumentParser()
    ap.add_argument("--paises", nargs="+", choices=list(PAISES.values()), default=list(PAISES.values()),
                    help="gera só estes países (padrão: todos)")
    chosen = set(ap.parse_args().paises)
    tables = {}
    for m, pais in [(m, p) for m, p in PAISES.items() if p in chosen]:
        base = C.BRASIL if m == "br" else C.market_dir(m)
        for loja, store in [("google_play", "google_play_store"), ("app_store", "app_store")]:
            p = base / store / "reviews_para_ia" / "reviews_critical_redacted.csv"
            if not p.exists():
                print(f"[{pais}/{loja}] sem críticas redigidas (passos 5 a 7); pulando")
                continue
            df = pd.read_csv(p, encoding="utf-8-sig", dtype={"at": str})
            df = df[[c for c in COLS if c in df]].sort_values(["app_mask_id", "at"])
            check(df, f"{pais}/{loja}")
            tables[(pais, loja)] = df
    stats = {}
    mapping = pd.read_csv(C.PATHS["mapping"], encoding="utf-8-sig")
    for m, pais in [(m, p) for m, p in PAISES.items() if p in chosen]:
        # lista de apps do país, MASCARADA (sem nome, ID nem desenvolvedor); contagens das próprias tabelas
        sample = (C.BR_BOTH_STORES if m == "br" else C.market_dir(m) / "apps_nas_duas_lojas" / "amostra_coleta.csv")
        if not sample.exists() or not any(k[0] == pais for k in tables):
            continue
        a = pd.read_csv(sample, encoding="utf-8-sig").merge(
            mapping[["app_mask_id", "appId"]], left_on="gp_app_id", right_on="appId")
        a = a[["app_mask_id", "gp_category"]].rename(columns={"gp_category": "categoria"})
        for loja in ("google_play", "app_store"):
            counts = tables[(pais, loja)].app_mask_id.value_counts() if (pais, loja) in tables else pd.Series(dtype=int)
            a[f"criticas_{loja}"] = a.app_mask_id.map(counts).fillna(0).astype(int)
        write_csv(a.sort_values("app_mask_id"), PUB / pais / "apps.csv")
    for (pais, loja), df in tables.items():  # só grava depois que TUDO passou na checagem
        folder = PUB / pais / loja
        shutil.rmtree(folder, ignore_errors=True)
        n_files = 0
        for mask, part in df.groupby("app_mask_id"):
            chunks = [part.iloc[i:i + ROWS_PER_FILE] for i in range(0, len(part), ROWS_PER_FILE)]
            for k, chunk in enumerate(chunks, 1):
                name = f"{mask}.csv" if len(chunks) == 1 else f"{mask}_parte{k}.csv"
                write_csv(chunk, folder / name)
                n_files += 1
        stats[f"{pais}/{loja}"] = {"criticas": int(len(df)), "apps": int(df.app_mask_id.nunique()), "arquivos": n_files}
        print(f"[{pais}/{loja}] {len(df)} críticas, {df.app_mask_id.nunique()} apps, {n_files} arquivos -> {folder}")
    shared = C.DATA / "mercados_internacionais" / "apps_em_varios_paises.csv"
    if shared.exists():
        s = pd.read_csv(shared, encoding="utf-8-sig").drop(columns=["app"])  # sem nome do app
        s = s.astype({c: "Int64" for c in s if c.startswith("criticas_")})
        write_csv(s, PUB / "mercados_internacionais" / "apps_em_varios_paises.csv")
    update_metrics("08b_publico_criticas", stats)


if __name__ == "__main__":
    main()
