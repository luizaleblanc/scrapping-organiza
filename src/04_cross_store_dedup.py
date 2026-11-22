"""Etapa 4 — Deduplicação cruzada Google Play x App Store (critério 4).

Camadas de matching (pareamento 1:1, melhor camada primeiro):
  exact             título normalizado == e desenvolvedor normalizado ==
  exact_title       título completo normalizado idêntico (desenvolvedor pode ter
                    razão social diferente entre lojas)
  normalized_brand  marca (nome-base) == e similaridade de desenvolvedor >= 0.75
  fuzzy_review      similaridade combinada >= 0.85 ou marca == com desenvolvedor
                    divergente -> só entra se aprovado em manual_match_decisions.csv
Saídas: data/apps_nas_duas_lojas/apps_both_stores.csv (1 linha por app, base da coleta),
        apps_single_store_excluded.csv e manual_match_decisions.csv (para revisão).
"""
import sys
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
from rules import update_metrics, write_csv  # noqa: E402
from text_norm import brand, norm, norm_dev  # noqa: E402

TIERS = ["exact", "exact_title", "normalized_brand", "fuzzy_review"]


def sim(a, b):
    return SequenceMatcher(None, a, b).ratio() if a and b else 0.0


def match(g, a):
    t_g, t_a = norm(g.title), norm(a.trackName)
    b_g, b_a = brand(g.title), brand(a.trackName)
    d_g, d_a = norm_dev(g.developer), norm_dev(a.artistName)
    dev = 1.0 if d_g and d_g == d_a else sim(d_g, d_a)
    combined = (max(sim(t_g, t_a), sim(b_g, b_a)) + dev) / 2
    if t_g == t_a and d_g == d_a:
        return "exact", 1.0
    if t_g == t_a:
        return "exact_title", combined
    if b_g and b_g == b_a and dev >= 0.75:
        return "normalized_brand", combined
    if combined >= 0.85 or (b_g and b_g == b_a):
        return "fuzzy_review", combined
    return None, combined


def load_manual():
    path = C.PATHS["manual_matches"]
    if not path.exists():
        return {}
    m = pd.read_csv(path, encoding="utf-8-sig", dtype=str).fillna("")
    return {(r.gp_app_id, r.as_track_id): r.decision.strip().casefold() for r in m.itertuples()}


def main():
    gp = pd.read_csv(C.PATHS["gp_eligible"], encoding="utf-8-sig")
    a_s = pd.read_csv(C.PATHS["as_eligible"], encoding="utf-8-sig")
    manual = load_manual()

    cands = []
    for gi, g in gp.iterrows():
        for ai, a in a_s.iterrows():
            tier, score = match(g, a)
            if tier:
                cands.append((TIERS.index(tier), -score, gi, ai, tier, score))
    cands.sort()
    used_g, used_a, rows, review = set(), set(), [], []
    for _, _, gi, ai, tier, score in cands:
        if gi in used_g or ai in used_a:
            continue
        g, a = gp.loc[gi], a_s.loc[ai]
        status = "auto_accepted"
        if tier == "fuzzy_review":
            decision = manual.get((g.appId, str(int(a.trackId))), "")
            review.append({"gp_app_id": g.appId, "gp_title": g.title, "gp_developer": g.developer,
                           "as_track_id": str(int(a.trackId)), "as_title": a.trackName,
                           "as_developer": a.artistName, "score": round(score, 3), "decision": decision})
            if decision != "yes":
                continue  # sem aprovação humana não há fusão
            status = "manual_accepted"
        used_g.add(gi)
        used_a.add(ai)
        rows.append({
            "unified_name": g.title, "gp_app_id": g.appId, "as_track_id": int(a.trackId),
            "as_bundle_id": a.bundleId, "gp_title": g.title, "as_title": a.trackName,
            "gp_developer": g.developer, "as_developer": a.artistName,
            "gp_category": g.genre, "as_category": a.primaryGenreName,
            "gp_ratings": g.ratings, "gp_reviews": g.reviews, "as_ratings": a.userRatingCount,
            "gp_updated": g.updated_utc, "as_updated": a.updated_utc,
            "gp_search_terms": g.search_terms, "as_search_terms": a.search_terms,
            "match_confidence": tier, "match_score": round(score, 3), "manual_check_status": status,
        })
    both = pd.DataFrame(rows).sort_values("unified_name")
    single = pd.concat([
        gp.drop(index=list(used_g)).assign(store="google_play_store", app_id=lambda d: d.appId)[
            ["store", "app_id", "title", "developer"]],
        a_s.drop(index=list(used_a)).assign(store="app_store", app_id=lambda d: d.trackId.astype(str),
                                            title=lambda d: d.trackName, developer=lambda d: d.artistName)[
            ["store", "app_id", "title", "developer"]],
    ]).assign(exclusion_reason="excluded_single_store_criterion_4")
    write_csv(both, C.PATHS["both_stores"])
    write_csv(single, C.PATHS["single_store"])
    write_csv(pd.DataFrame(review, columns=["gp_app_id", "gp_title", "gp_developer", "as_track_id",
                                            "as_title", "as_developer", "score", "decision"]),
              C.PATHS["manual_matches"])
    pending = sum(1 for r in review if r["decision"] not in {"yes", "no"})
    update_metrics("04_cross_store", {
        "google_play_eligible": int(len(gp)), "app_store_eligible": int(len(a_s)),
        "both_stores": int(len(both)),
        "by_match_confidence": {k: int(v) for k, v in both.match_confidence.value_counts().items()},
        "fuzzy_pending_manual_review": pending,
        "single_store_google_play": int((single.store == "google_play_store").sum()),
        "single_store_app_store": int((single.store == "app_store").sum()),
    })
    pd.set_option("display.width", 250)
    print(both[["unified_name", "as_title", "match_confidence", "manual_check_status"]].to_string(index=False))
    print(f"\nNas duas lojas: {len(both)} | pendentes de revisão manual: {pending} "
          f"(edite a coluna decision com yes/no em {C.PATHS['manual_matches']} e rode de novo)")
    if review:
        print(pd.DataFrame(review)[["gp_title", "gp_developer", "as_title", "as_developer", "decision"]].to_string(index=False))


if __name__ == "__main__":
    main()
