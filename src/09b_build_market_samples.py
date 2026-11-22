"""Etapa 9b — Lista de apps para coletar reviews em cada país extra (us, es, mx).

Entram os apps que a busca traduzida ENCONTROU e que são ELEGÍVEIS naquele país
(data/mercados_internacionais/<país>/apps_nas_duas_lojas/apps_both_stores.csv, já com a revisão manual
dos pares). Se existir a validação da pesquisadora
(data/brasil/apps_nas_duas_lojas/apps_novos_outros_idiomas_validado.csv), os apps marcados
com decisao = "nao" saem.
Saída: data/mercados_internacionais/<país>/apps_nas_duas_lojas/amostra_coleta.csv (lida pelos passos 5 e 5b).
Rode sem MARKET.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
from rules import update_metrics, write_csv  # noqa: E402


def main():
    if C.MARKET != "br":
        raise SystemExit("Rode este script sem MARKET (ou MARKET=br).")
    rejected = set()
    if C.MULTILANG_VALIDATED.exists():
        val = pd.read_csv(C.MULTILANG_VALIDATED, encoding="utf-8-sig")
        dec = val.decisao.astype(str).str.strip().str.casefold()
        if not dec.isin({"sim", "nao", "não"}).all():
            raise SystemExit("A coluna decisao do arquivo validado deve ter só 'sim' ou 'nao'.")
        rejected = set(val.loc[dec.isin({"nao", "não"}), "gp_app_id"])
    else:
        print(f"AVISO: sem validação ({C.MULTILANG_VALIDATED.name}); entram todos os elegíveis.")
    rejected |= set(C.EXCLUDE_INTERNATIONAL_APPS)  # higienização manual registrada no config
    stats = {}
    for m in C.EXTRA_MARKETS:
        d = C.market_dir(m) / "apps_nas_duas_lojas"
        both = pd.read_csv(d / "apps_both_stores.csv", encoding="utf-8-sig")
        sample = both[~both.gp_app_id.isin(rejected)]
        write_csv(sample, d / "amostra_coleta.csv")
        stats[m] = {"elegiveis_nas_duas_lojas": int(len(both)), "removidos_na_validacao": int(len(both) - len(sample)),
                    "total": int(len(sample))}
        print(f"[{m}] {len(both)} elegíveis - {len(both) - len(sample)} recusados na validação = {len(sample)} apps")
    update_metrics("09b_amostras_outros_idiomas", stats)


if __name__ == "__main__":
    main()
