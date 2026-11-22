"""Map the approved Google Play sample (data/private/app_mapping.csv) to App Store apps.

Replaces keyword discovery: App Store candidates = the same 38 apps used in ai_share.
"""
import difflib, re, sys, time, unicodedata
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd, requests

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data/private/app_mapping.csv"
OUT = ROOT / "data/raw/app_store/candidates.csv"
API = "https://itunes.apple.com/search"

def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().casefold()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()

def brand(title):
    return norm(re.split(r"[:\-–—|(]", title)[0])

def search(term, country):
    for i in range(4):
        try:
            r = requests.get(API, params={"term": term, "entity": "software", "country": country, "limit": 15}, timeout=25)
            r.raise_for_status(); return r.json().get("results", [])
        except Exception:
            time.sleep(2 ** i)
    return []

CRYPTO_USD = re.compile(r"(crypto|cripto|criptomoedas?|bitcoin|btc|ethereum|blockchain|stablecoin|usdt|usdc|token|nft|dolar|dollar|usd|conta em dolar|cambio|forex)")
rows = []
now = datetime.now(timezone.utc).isoformat()
for _, a in pd.read_csv(SRC, encoding="utf-8-sig").iterrows():
    best, best_score, best_country = None, 0.0, None
    for country in ("br",):  # somente App Store Brasil
        for res in search(a.title, country):
            t = res.get("trackName", "")
            score = difflib.SequenceMatcher(None, norm(a.title), norm(t)).ratio()
            ba, bt = brand(a.title), brand(t)
            if ba and bt and (ba == bt or bt.startswith(ba) or ba.startswith(bt)):
                score = max(score, 0.85)
            else:
                score = min(score, 0.7)  # marca diferente: nunca aceita automaticamente
            if res.get("primaryGenreName") == "Finance":
                score += 0.05
            if score > best_score:
                best, best_score, best_country = res, score, country
        time.sleep(3.2)
        if best_score >= 0.9:
            break
    b0 = best or {}
    txt = norm(f"{b0.get('trackName','')} {b0.get('artistName','')}")
    if CRYPTO_USD.search(txt):
        best_score = -1  # moedas digitais / dólar: fora do escopo
    status = "excluded_crypto_usd" if best_score < 0 else None
    status = status or ("matched" if best_score >= 0.8 else ("manual_review" if best_score >= 0.6 else "not_found"))
    b = best or {}
    rows.append({
        "app_mask_id": a.app_mask_id, "google_play_app_id": a.appId, "google_play_title": a.title,
        "trackId": b.get("trackId"), "bundleId": b.get("bundleId"), "trackName": b.get("trackName"),
        "artistName": b.get("artistName"), "primaryGenreName": b.get("primaryGenreName"),
        "averageUserRating": b.get("averageUserRating"), "userRatingCount": b.get("userRatingCount"),
        "country": best_country, "trackViewUrl": b.get("trackViewUrl"),
        "match_score": round(best_score, 3), "match_status": status, "collected_at": now,
    })
    print(f"{a.app_mask_id} {status:13} {best_score:.2f} {a.title} -> {b.get('trackName')}")

df = pd.DataFrame(rows)
df.to_csv(ROOT / "data/raw/app_store/candidates_mapped_audit.csv", index=False, encoding="utf-8-sig")
df[df.match_status.eq("matched")].to_csv(OUT, index=False, encoding="utf-8-sig")
print(df.match_status.value_counts().to_string())
