# tcg-price-data

Public daily price snapshots for the [TCG Slayer](https://thetcgslayer.com/portfolio) Collection Value Tracker (Pillar 2 — "Bloomberg for collectibles").

- **`tracked-cards.json`** — curated chase-card list + display metadata.
- **`price-history.json`** — `{ cardId: { "YYYY-MM-DD": marketPrice } }`, appended daily.
- **`snapshot.py`** — fetches current TCGplayer market prices from [pokemontcg.io](https://pokemontcg.io) (key-less; set `POKEMONTCG_API_KEY` secret for higher limits).
- **`.github/workflows/snapshot.yml`** — runs `snapshot.py` daily at 09:00 UTC and commits the result.

History **cannot be backfilled**, so this repo exists to accumulate it going forward. The tracker fetches `price-history.json` from the raw GitHub URL (public repo → CORS-friendly, updates on every commit, no site rebuild).

Prices are seller/market data via TCGplayer and are informational only. Not affiliated with Nintendo / The Pokémon Company.
