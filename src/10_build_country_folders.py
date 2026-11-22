"""Etapa 10 — Uma pasta por país, só com as reviews CRÍTICAS, separadas por app.

data/brasil/ e data/mercados_internacionais/<país>/ (arquivos na raiz da pasta do país):
  apps_elegiveis.csv            apps encontrados e elegíveis naquele país (nas duas lojas),
                                com máscara, nome e quantas críticas cada um teve por loja
  criticas.csv                  todas as críticas do país num só arquivo (colunas app e loja)
E data/mercados_internacionais/apps_em_varios_paises.csv: apps elegíveis em mais de um
país (incluindo o Brasil), com o total de críticas em cada um.
Usa as cópias redigidas (passo 7): sem dados do avaliador e com data sem hora.
Países sem coleta ainda (passos 5 a 7) ganham só o apps_elegiveis.csv.
Fica em data/ (não versionado): os nomes dos apps aparecem aqui. Rode sem MARKET.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
from rules import update_metrics, write_csv  # noqa: E402

PAISES = {"br": "brasil", "us": "estados_unidos", "es": "espanha", "mx": "mexico"}


def sources(m):
    base = C.BRASIL if m == "br" else C.market_dir(m)
    return {"sample": base / "apps_nas_duas_lojas" / ("apps_both_stores.csv" if m == "br" else "amostra_coleta.csv"),
            "google_play": base / "google_play_store" / "reviews_para_ia" / "reviews_critical_redacted.csv",
            "app_store": base / "app_store" / "reviews_para_ia" / "reviews_critical_redacted.csv"}


def read(path):
    return pd.read_csv(path, encoding="utf-8-sig") if path.exists() else None


def main():
    if C.MARKET != "br":
        raise SystemExit("Rode este script sem MARKET (ou MARKET=br).")
    mapping = pd.read_csv(C.PATHS["mapping"], encoding="utf-8-sig")
    stats = {}
    for m, pais in PAISES.items():
        src = sources(m)
        sample = read(src["sample"])
        if sample is None:
            print(f"[{pais}] sem lista de apps ({src['sample'].name}); pulando")
            continue
        folder = C.BRASIL if m == "br" else C.market_dir(m)
        crit = {loja: read(p) for loja, p in [("google_play", src["google_play"]), ("app_store", src["app_store"])]}
        if all(df is None for df in crit.values()) and (folder / "criticas.csv").exists():
            print(f"[{pais}] arquivos intermediários já apagados; mantendo {folder / 'criticas.csv'}")
            continue
        for f in ("apps_elegiveis.csv", "criticas.csv"):  # sempre gerados do zero
            (folder / f).unlink(missing_ok=True)
        apps = sample.merge(mapping[["app_mask_id", "appId"]], left_on="gp_app_id", right_on="appId", how="left")
        for loja, df in crit.items():
            if df is not None:
                df = df[df.app_mask_id.isin(set(apps.app_mask_id))]
                crit[loja] = df
                apps[f"criticas_{loja}"] = apps.app_mask_id.map(df.app_mask_id.value_counts()).fillna(0).astype(int)
        cols = ["app_mask_id", "unified_name", "gp_app_id", "as_track_id", "gp_developer", "as_developer",
                "gp_category"] + [c for c in apps if c.startswith("criticas_")]
        write_csv(apps[cols].sort_values("unified_name"), folder / "apps_elegiveis.csv")
        frames = [df.assign(loja=loja) for loja, df in crit.items() if df is not None]
        n = 0
        if frames:  # um único arquivo por país: as duas lojas juntas, com o nome do app
            allc = pd.concat(frames, ignore_index=True).merge(
                apps[["app_mask_id", "unified_name"]].rename(columns={"unified_name": "app"}), on="app_mask_id")
            cols = ["app_mask_id", "app", "loja", "score", "content", "lang", "at", "compound"]
            write_csv(allc[[c for c in cols if c in allc]].sort_values(["app", "loja", "at"]),
                      folder / "criticas.csv")
            n = len(allc)
        stats[pais] = {"apps": int(len(apps)), "criticas": int(n)}
        print(f"[{pais}] {len(apps)} apps, {n} críticas -> {folder}")
    shared = build_shared_apps()
    stats["apps_em_varios_paises"] = int(len(shared))
    update_metrics("10_pastas_por_pais", stats)


def build_shared_apps():
    """Apps elegíveis em mais de um país (mesmo appId da Google Play), com as críticas
    de cada país por loja. Saída: data/mercados_internacionais/apps_em_varios_paises.csv"""
    frames = []
    for m, pais in PAISES.items():
        path = (C.BRASIL if m == "br" else C.market_dir(m)) / "apps_elegiveis.csv"
        if path.exists():
            frames.append(pd.read_csv(path, encoding="utf-8-sig").assign(pais=pais))
    df = pd.concat(frames, ignore_index=True)
    for loja in ("google_play", "app_store"):
        df[f"criticas_{loja}"] = df.get(f"criticas_{loja}", 0)
    df["criticas"] = df.criticas_google_play.fillna(0).astype(int) + df.criticas_app_store.fillna(0).astype(int)
    n_paises = df.groupby("gp_app_id").pais.transform("nunique")
    df = df[n_paises > 1]
    wide = df.pivot_table(index="gp_app_id", columns="pais", values="criticas", aggfunc="sum")
    wide = wide[[p for p in PAISES.values() if p in wide]].astype("Int64").rename(columns=lambda p: f"criticas_{p}")
    info = df.groupby("gp_app_id").agg(
        app_mask_id=("app_mask_id", "first"), app=("unified_name", "first"),
        paises=("pais", lambda s: " + ".join(p for p in PAISES.values() if p in set(s))),
        n_paises=("pais", "nunique"))
    out = info.join(wide).reset_index(drop=True).sort_values(["n_paises", "app"], ascending=[False, True])
    # vazio = app não é elegível naquele país; 0 = elegível, mas sem críticas
    write_csv(out, C.DATA / "mercados_internacionais" / "apps_em_varios_paises.csv")
    print(f"{len(out)} apps em mais de um país -> mercados_internacionais/apps_em_varios_paises.csv")
    return out


if __name__ == "__main__":
    main()
