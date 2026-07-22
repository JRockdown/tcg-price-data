#!/usr/bin/env python3
"""
Daily Pokémon-card price snapshot for the TCG Slayer Collection Value Tracker.

- Reads tracked-cards.json (curated chase-card list + metadata). Seeds it on first run.
- Fetches current TCGplayer market price for each tracked card from pokemontcg.io.
- Appends today's price to price-history.json:  { cardId: { "YYYY-MM-DD": price, ... } }

No dependencies beyond the stdlib. pokemontcg.io works key-less (add POKEMONTCG_API_KEY
env for higher rate limits). History can't be backfilled, so this runs daily via Actions.
"""
import json, os, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone

API = "https://api.pokemontcg.io/v2/cards"
DIR = os.path.dirname(os.path.abspath(__file__))
TRACKED = os.path.join(DIR, "tracked-cards.json")
HISTORY = os.path.join(DIR, "price-history.json")
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")

# Iconic, high-demand Pokémon used only to SEED the tracked set on first run.
SEED_NAMES = ["charizard", "pikachu", "mewtwo", "umbreon", "rayquaza", "lugia",
              "gengar", "eevee", "mew", "blastoise", "venusaur", "gyarados",
              "dragonite", "sylveon", "gardevoir", "greninja"]
SEED_MIN_PRICE = 20.0     # only track cards worth caring about
SEED_PER_NAME = 8         # top-N priciest printings per Pokémon
SEED_CAP = 150            # overall ceiling

HEADERS = {"User-Agent": "tcg-price-data/1.0 (+github.com/JRockdown/tcg-price-data)"}
if os.environ.get("POKEMONTCG_API_KEY"):
    HEADERS["X-Api-Key"] = os.environ["POKEMONTCG_API_KEY"]


def get(url):
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.load(r)
        except Exception as e:
            if attempt == 2:
                print(f"  ! fetch failed: {url[:80]} -> {e}")
                return {}
            time.sleep(3 * (attempt + 1))
    return {}


def market(card):
    prices = (card.get("tcgplayer") or {}).get("prices") or {}
    for k in ("holofoil", "reverseHolofoil", "normal",
              "1stEditionHolofoil", "unlimitedHolofoil"):
        m = prices.get(k) or {}
        v = m.get("market") or m.get("mid") or m.get("low")
        if v:
            return round(float(v), 2)
    return None


def seed_tracked():
    print("Seeding curated chase-card list (first run)...")
    picked = {}
    for name in SEED_NAMES:
        q = urllib.parse.quote(f'name:{name} (rarity:"Rare Holo" OR rarity:"Illustration Rare" '
                               f'OR rarity:"Special Illustration Rare" OR rarity:"Rare Holo VMAX" '
                               f'OR rarity:"Rare Secret")')
        data = get(f"{API}?q={q}&pageSize=60").get("data") or []
        rows = []
        for c in data:
            mp = market(c)
            if mp and mp >= SEED_MIN_PRICE:
                rows.append((mp, c))
        rows.sort(key=lambda r: -r[0])
        for mp, c in rows[:SEED_PER_NAME]:
            picked[c["id"]] = {
                "id": c["id"], "name": c.get("name", ""),
                "set": (c.get("set") or {}).get("name", ""),
                "number": c.get("number", ""), "rarity": c.get("rarity", ""),
                "img": (c.get("images") or {}).get("small", ""),
            }
        print(f"  {name}: +{len(rows[:SEED_PER_NAME])}")
        time.sleep(0.3)
    tracked = list(picked.values())[:SEED_CAP]
    json.dump(tracked, open(TRACKED, "w"), indent=1)
    print(f"Seeded {len(tracked)} cards -> tracked-cards.json")
    return tracked


def snapshot(tracked, history):
    ids = [c["id"] for c in tracked]
    prices = {}
    # batch ~12 ids per query to keep URLs sane
    for i in range(0, len(ids), 12):
        batch = ids[i:i + 12]
        q = urllib.parse.quote(" OR ".join(f'id:"{cid}"' for cid in batch))
        data = get(f"{API}?q={q}&pageSize=25").get("data") or []
        for c in data:
            mp = market(c)
            if mp:
                prices[c["id"]] = mp
        time.sleep(0.3)
    got = 0
    for cid, mp in prices.items():
        history.setdefault(cid, {})[TODAY] = mp
        got += 1
    print(f"Snapshotted {got}/{len(ids)} card prices for {TODAY}")
    return got


def main():
    tracked = json.load(open(TRACKED)) if os.path.exists(TRACKED) else []
    if not tracked:
        tracked = seed_tracked()
    history = json.load(open(HISTORY)) if os.path.exists(HISTORY) else {}
    got = snapshot(tracked, history)
    if got == 0:
        print("No prices captured — leaving history unchanged.")
        sys.exit(1)
    json.dump(history, open(HISTORY, "w"), separators=(",", ":"))
    print(f"Wrote price-history.json ({len(history)} cards tracked).")


if __name__ == "__main__":
    main()
