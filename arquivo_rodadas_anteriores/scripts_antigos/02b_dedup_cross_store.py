"""Deduplicação cruzada App Store x Google Play (critério 4: disponível nas duas lojas).

Camadas (nenhuma fusão automática fora delas):
  exact            título normalizado == e desenvolvedor normalizado ==
  normalized_brand marca (nome-base) == e similaridade de desenvolvedor >= 0.75
  fuzzy_review     similaridade combinada título/desenvolvedor >= 0.85, ou marca == com
                   desenvolvedor divergente -> exige conferência humana
Pareamento 1:1 guloso (melhor camada, depois maior score).
"""
import json
import sys
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
from text_norm import brand, has_term, norm, norm_dev  # noqa: E402

TIER_RANK = {"exact": 0, "normalized_brand": 1, "fuzzy_review": 2}


def sim(a, b):
    return SequenceMatcher(None, a, b).ratio() if a and b else 0.0


def match_pair(gp, a_s):
    t_gp, t_as = norm(gp.title), norm(a_s.trackName)
    b_gp, b_as = brand(gp.title), brand(a_s.trackName)
    d_gp, d_as = norm_dev(gp.developer), norm_dev(a_s.artistName)
    dev_sim = max(sim(d_gp, d_as), 1.0 if d_gp and d_gp == d_as else 0.0)
    title_sim = max(sim(t_gp, t_as), sim(b_gp, b_as))
    combined = (title_sim + dev_sim) / 2
    if t_gp == t_as and d_gp == d_as:
        return "exact", 1.0, dev_sim
    if b_gp and b_gp == b_as and dev_sim >= 0.75:
        return "normalized_brand", combined, dev_sim
    if combined >= 0.85 or (b_gp and b_gp == b_as):
        return "fuzzy_review", combined, dev_sim
    return None, combined, dev_sim


def gp_exclusion(row):
    """Mesmas regras da App Store aplicadas à base Google Play."""
    title, text = norm(row.title), f"{norm(row.title)} {norm(row.developer)}"
    if has_term(text, C.EXCLUDE_CONFLICT_OF_INTEREST):
        return "conflict_of_interest_organiza_ai"
    if norm(row.genre) not in C.FINANCE_CATEGORIES:
        return "wrong_category_productivity_or_game" if (norm(row.genre) in {"productivity", "produtividade", "games", "jogos"}
                                                         or has_term(title, C.EXCLUDE_PRODUCTIVITY_GAMES)) else "wrong_category_other"
    for reason, terms in [("excluded_financial_type_bank", C.EXCLUDE_BANKS),
                          ("excluded_financial_type_wallet_payment", C.EXCLUDE_WALLETS_PAYMENTS),
                          ("excluded_financial_type_brokerage_crypto", C.EXCLUDE_BROKERAGE_CRYPTO),
                          ("excluded_b2b_accounting_credit", C.EXCLUDE_B2B_CREDIT)]:
        hit = has_term(text, terms)
        if hit:
            return f"{reason}:{hit}"
    return ""


def main():
    a_store = pd.read_csv(C.CLEAN_OUTPUT["as_clean"], encoding="utf-8-sig")
    gp_all = pd.read_csv(C.GOOGLE_PLAY_INPUT, encoding="utf-8-sig").drop_duplicates("appId")
    ai_share = set(pd.read_csv(C.AI_SHARE_MAPPING, encoding="utf-8-sig").appId) if C.AI_SHARE_MAPPING.exists() else set()
    gp_all["exclusion_reason"] = gp_all.apply(gp_exclusion, axis=1)
    gp_all[gp_all.exclusion_reason.ne("")].to_csv(C.CLEAN_OUTPUT["gp_excluded"], index=False, encoding="utf-8-sig")
    gp = gp_all[gp_all.exclusion_reason.eq("")].reset_index(drop=True)

    cands = []
    for gi, g in gp.iterrows():
        for ai, a in a_store.iterrows():
            tier, score, dev_sim = match_pair(g, a)
            if tier:
                cands.append((TIER_RANK[tier], -score, gi, ai, tier, score, dev_sim))
    cands.sort()
    used_gp, used_as, rows = set(), set(), []
    for _, _, gi, ai, tier, score, dev_sim in cands:
        if gi in used_gp or ai in used_as:
            continue
        used_gp.add(gi)
        used_as.add(ai)
        g, a = gp.loc[gi], a_store.loc[ai]
        rows.append({
            "unified_name": brand(a.trackName).title() or a.trackName,
            "gp_app_id": g.appId, "as_track_id": int(a.trackId), "as_bundle_id": a.bundleId,
            "gp_title": g.title, "as_title": a.trackName,
            "gp_developer": g.developer, "as_developer": a.artistName,
            "gp_category": g.genre, "as_category": a.primaryGenreName,
            "gp_reviews": g.reviews, "as_reviews": a.userRatingCount,
            "gp_updated": g.get("updated_utc"), "as_updated": a.currentVersionReleaseDate,
            "terms_found": f"GP:{g.matched_terms} | AS:{a.as_terms_found}",
            "match_confidence": tier, "match_score": round(score, 3), "developer_similarity": round(dev_sim, 3),
            "manual_check_status": "REVIEW_REQUIRED" if tier == "fuzzy_review" else "auto_accepted",
            "in_ai_share_sample": g.appId in ai_share,
        })
    cross = pd.DataFrame(rows).sort_values(["match_confidence", "unified_name"])

    single = pd.concat([
        a_store.drop(index=list(used_as)).assign(
            store="app_store", app_id=lambda d: d.trackId.astype("Int64").astype(str),
            title=lambda d: d.trackName, developer=lambda d: d.artistName, category=lambda d: d.primaryGenreName,
            exclusion_reason="excluded_single_store_app_store_only")[["store", "app_id", "title", "developer", "category", "exclusion_reason"]],
        gp.drop(index=list(used_gp)).assign(
            store="google_play", app_id=lambda d: d.appId, category=lambda d: d.genre,
            exclusion_reason="excluded_single_store_google_play_only")[["store", "app_id", "title", "developer", "category", "exclusion_reason"]],
    ], ignore_index=True)

    cross.to_csv(C.CLEAN_OUTPUT["cross"], index=False, encoding="utf-8-sig")
    single.to_csv(C.CLEAN_OUTPUT["single"], index=False, encoding="utf-8-sig")

    stage = {
        "google_play_input": C.GOOGLE_PLAY_INPUT.relative_to(C.ROOT).as_posix(),
        "google_play_total": int(len(gp_all)),
        "google_play_removed_by_reason": {k: int(v) for k, v in
                                          gp_all.loc[gp_all.exclusion_reason.ne(""), "exclusion_reason"].str.split(":").str[0].value_counts().items()},
        "google_play_eligible": int(len(gp)),
        "app_store_clean": int(len(a_store)),
        "cross_platform_final": int(len(cross)),
        "by_match_confidence": {k: int(v) for k, v in cross.match_confidence.value_counts().items()},
        "fuzzy_review_pending": int(cross.manual_check_status.eq("REVIEW_REQUIRED").sum()),
        "cross_in_ai_share_sample": int(cross.in_ai_share_sample.sum()),
        "excluded_single_store_app_store_only": int(single.store.eq("app_store").sum()),
        "excluded_single_store_google_play_only": int(single.store.eq("google_play").sum()),
    }
    path = C.CLEAN_OUTPUT["metrics"]
    metrics = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    metrics["generated_at"] = datetime.now(timezone.utc).isoformat()
    metrics["stage_02b_cross_store_dedup"] = stage
    path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(stage, ensure_ascii=False, indent=2))
    pd.set_option("display.width", 250)
    print(cross[["unified_name", "gp_title", "as_title", "match_confidence", "match_score", "manual_check_status"]].to_string(index=False))


if __name__ == "__main__":
    main()
