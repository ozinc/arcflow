"""
Synthesized fixture for the algo-trading LLM harness cookbook.

Shape:
- 8 symbols across 3 sectors (Tech / Energy / Health), 60 trading days
  of OHLCV with a deterministic seeded random walk.
- Fundamentals per symbol at day 0 (eps, book_value) with one mid-period
  restatement on `ENGY-02` at day 35 (the planted look-ahead landmine —
  the new eps would have been "wrong" to use before day 35 entered the WAL).
- Synthesized news-sentiment facts on 6 days for 4 symbols, tagged
  `_observation_class = "predicted"` with low `_confidence` to represent
  what an LLM/sentiment model would emit. Technical signals are tagged
  `_observation_class = "observed"` at high confidence.

The fixture is *small enough to load in <1 second* but *rich enough to
exercise every pattern in the three steps*: AS OF replay, cascading LIVE
views, confidence-weighted ER.
"""

import math
import random
from arcflow import ArcFlow


SYMBOLS = [
    ("TECH-01", "Tech",    150.0),
    ("TECH-02", "Tech",    220.0),
    ("TECH-03", "Tech",     85.0),
    ("ENGY-01", "Energy",  110.0),
    ("ENGY-02", "Energy",   75.0),
    ("HLTH-01", "Health",  340.0),
    ("HLTH-02", "Health",  180.0),
    ("HLTH-03", "Health",   95.0),
]
DAYS = 60
RESTATEMENT_DAY = 35


def make_db(data_dir: str | None = None):
    """Build the world state. data_dir=None → in-memory; pass a path for
    AS OF replay (the WAL only lives on persistent instances).
    """
    rng = random.Random(7)
    db = ArcFlow(data_dir) if data_dir else ArcFlow()

    # --- 1. Symbols + initial fundamentals via bulk (cold history, no WAL) ---
    symbol_nodes = db.bulk_create_nodes([
        (["Symbol"], {
            "ticker": tkr,
            "sector": sec,
            "init_close": init,
        })
        for tkr, sec, init in SYMBOLS
    ])
    by_ticker = {SYMBOLS[i][0]: nid for i, nid in enumerate(symbol_nodes)}

    fund_nodes = db.bulk_create_nodes([
        (["Fundamental"], {
            "ticker": tkr,
            "as_of_day": 0,
            "eps": round(rng.uniform(2.0, 8.0), 2),
            "book_value": round(rng.uniform(30.0, 90.0), 2),
            # `original` marks the day-0 fundamentals; the restatement on
            # ENGY-02 will land via `execute()` at day 35 so it shows up in
            # the WAL and the AS OF replay catches it.
            "revision": "original",
        })
        for tkr, _sec, _init in SYMBOLS
    ])
    db.bulk_create_relationships(
        "HAS_FUNDAMENTAL",
        [(by_ticker[SYMBOLS[i][0]], fnid, {}) for i, fnid in enumerate(fund_nodes)],
    )

    # --- 2. OHLCV bars — 8 symbols × 60 days = 480 nodes, bulk-loaded ---
    bar_specs = []
    for tkr, sec, init_close in SYMBOLS:
        price = init_close
        for d in range(DAYS):
            shock = rng.gauss(0.0, init_close * 0.012)  # ~1.2 % daily vol
            price = max(1.0, price + shock)
            open_ = price * (1.0 + rng.uniform(-0.003, 0.003))
            high  = max(price, open_) * (1.0 + rng.uniform(0.0, 0.005))
            low   = min(price, open_) * (1.0 - rng.uniform(0.0, 0.005))
            volume = int(rng.uniform(8e5, 5e6))
            bar_specs.append((["DailyBar"], {
                "ticker": tkr,
                "sector": sec,
                "day_idx": d,
                "open": round(open_, 3),
                "high": round(high,  3),
                "low":  round(low,   3),
                "close": round(price, 3),
                "volume": volume,
            }))
    bar_nodes = db.bulk_create_nodes(bar_specs)

    # Link Symbol → bars (cheap path; sector/day_idx live on the bar properties
    # for window-function queries).
    bar_to_symbol = []
    for i, spec in enumerate(bar_specs):
        ticker = spec[1]["ticker"]
        bar_to_symbol.append((by_ticker[ticker], bar_nodes[i], {}))
    db.bulk_create_relationships("HAS_BAR", bar_to_symbol)

    # --- 3. Synthesized sentiment facts ("predicted" facts from an LLM) ---
    # 6 news events across 4 tickers, each at low confidence, tagged
    # `predicted` so the fusion query can distinguish them from technical
    # (observed) signals.
    sentiment_specs = [
        ("TECH-01",  8, +0.42, 0.55, "earnings beat rumor"),
        ("TECH-01", 22, -0.18, 0.40, "supply-chain article"),
        ("TECH-03", 12, +0.61, 0.62, "product launch leak"),
        ("ENGY-02", 30, +0.30, 0.45, "buyback chatter"),
        ("ENGY-02", 38, -0.55, 0.70, "fraud investigation report"),
        ("HLTH-02", 44, +0.25, 0.50, "FDA decision speculation"),
    ]
    news_nodes = db.bulk_create_nodes([
        (["NewsSentiment"], {
            "ticker": tkr,
            "day_idx": day,
            "score": score,
            "_confidence": conf,
            "_observation_class": "predicted",
            "source": "sentiment_llm_v1",
            "headline_topic": topic,
        })
        for tkr, day, score, conf, topic in sentiment_specs
    ])
    db.bulk_create_relationships(
        "MENTIONS",
        [(by_ticker[s[0]], news_nodes[i], {}) for i, s in enumerate(sentiment_specs)],
    )

    return db, by_ticker


def stats(db):
    out = {}
    for label, q in [
        ("symbols",      "MATCH (s:Symbol) RETURN count(*) AS n"),
        ("fundamentals", "MATCH (f:Fundamental) RETURN count(*) AS n"),
        ("bars",         "MATCH (b:DailyBar) RETURN count(*) AS n"),
        ("news",         "MATCH (n:NewsSentiment) RETURN count(*) AS n"),
    ]:
        rows = list(db.execute(q))
        out[label] = int(rows[0]["n"])
    return out


if __name__ == "__main__":
    db, _ = make_db()
    for k, v in stats(db).items():
        print(f"  {k:14s}  {v:,}")
    db.close()
