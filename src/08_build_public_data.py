"""Etapa 8 — Gera data/publico/: a única parte dos dados que vai para o GitHub.

Nada aqui permite saber qual app é qual:
- só os apps da amostra final (os reprovados na triagem não são listados), SEM trackId, bundleId, trackName, artistName, appId, title,
  developer, URLs (trackViewUrl/url) ou descrição;
- cada app recebe um código opaco sorteado por loja (GP_xxx / AS_xxx), sem relação
  com as máscaras APP_xxx das reviews;
- funil só com totais, sem contagens por app (contagens por app identificam o app);
- reviews críticas redigidas, com data sem hora.
Os arquivos completos ficam só na máquina da pesquisadora (ver .gitignore).
"""
import json
import secrets
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
from rules import write_csv  # noqa: E402

PUB = C.DATA / "publico"


def opaque_ids(n, prefix):
    ids = [f"{prefix}_{i:03d}" for i in range(1, n + 1)]
    secrets.SystemRandom().shuffle(ids)
    return ids


def sample_apps(store, eligible_key, key_col, both_col, category_col, prefix, both):
    """Só os apps da amostra final (presentes nas duas lojas). Os reprovados na
    triagem não são listados; suas quantidades por motivo estão em funil.json."""
    el = pd.read_csv(C.PATHS[eligible_key], encoding="utf-8-sig")
    keep = set(both[both_col].astype(str))
    df = el[el[key_col].astype(str).isin(keep)].reset_index(drop=True)
    if "discovery_source" not in df:
        df["discovery_source"] = "search_strings"
    out = pd.DataFrame({
        "codigo_app": opaque_ids(len(df), prefix),
        "loja": store,
        "categoria": df[category_col].values,
        "strings_que_encontraram": df.term_ids.fillna("").values,
        "origem": df.discovery_source.fillna("search_strings").values,
    }).sort_values("codigo_app")
    return out


def main():
    PUB.mkdir(parents=True, exist_ok=True)
    both = pd.read_csv(C.PATHS["both_stores"], encoding="utf-8-sig")
    for old in ("triagem_google_play_store.csv", "triagem_app_store.csv"):
        (PUB / old).unlink(missing_ok=True)
    gp = sample_apps("google_play_store", "gp_eligible", "appId", "gp_app_id", "genre", "GP", both)
    a_s = sample_apps("app_store", "as_eligible", "trackId", "as_track_id", "primaryGenreName", "AS", both)
    write_csv(gp, PUB / "amostra_apps_google_play_store.csv")
    write_csv(a_s, PUB / "amostra_apps_app_store.csv")
    amostra = (both.groupby(["gp_category", "match_confidence"]).size()
               .rename("apps").reset_index()
               .rename(columns={"gp_category": "categoria", "match_confidence": "como_o_par_foi_confirmado"}))
    write_csv(amostra, PUB / "amostra_40_apps_resumo.csv")

    # Reviews críticas: copia as versões redigidas (já sem dados do avaliador e sem hora)
    # As críticas públicas (em tabelas pequenas por país, loja e app) são geradas pelo 08b.

    m = json.loads(C.PATHS["metrics"].read_text(encoding="utf-8"))
    def strip(d):
        if isinstance(d, dict):
            return {k: strip(v) for k, v in d.items()
                    if not (k.endswith("_by_app_mask") or k.startswith("source_by_app"))}
        return d
    (PUB / "funil.json").write_text(json.dumps(strip(m), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"data/publico/: amostra GP={len(gp)} AS={len(a_s)} apps (resumo={int(amostra.apps.sum())})")
    for f in sorted(PUB.iterdir()):
        print("  ", f.name)


if __name__ == "__main__":
    main()
