"""
Shared fixture for the Algo-Trading World Model cookbook.

The fixture is a small, *honest* operational world model for an LLM-driven
trading agent. It distinguishes the three epistemic states that ArcFlow
makes first-class on every fact (see /concepts/world-model):

    observed   — directly measured. Trades from the tape, OHLCV bars,
                 day-zero fundamentals received from a trusted source.
                 _confidence = 0.95-1.00.

    inferred   — derived by reasoning over observed facts. Rolling stats,
                 regime classifications, cross-sectional ranks. The
                 cookbook computes these via WorldCypher queries; in a
                 real harness they would be written back as nodes with
                 _observation_class = 'inferred'.
                 _confidence = 0.70-0.85.

    predicted  — model output, statistical projection, LLM emission.
                 News-sentiment scores, regime forward-looks, earnings
                 surprise forecasts. Useful for planning, never ground
                 truth.
                 _confidence = 0.30-0.70.

Shape:
- 8 symbols across 3 sectors (Tech / Energy / Health), 60 trading days of
  OHLCV with a deterministic seeded random walk. Bars are 'observed'.
- Fundamentals per symbol at day 0 (eps, book_value), 'observed'. One
  mid-period restatement on ENGY-02 at day 35 — the planted look-ahead-
  bias landmine for step 1.
- 6 news-sentiment facts from two distinct LLM sources
  (sentiment_llm_v1 = mainstream news, sentiment_llm_v2 = social signal)
  tagged 'predicted' at LLM-realistic confidences (0.40-0.70).
- 4 regime classifications per symbol from a hypothetical HMM
  (regime_hmm_v1) at spaced day_idx values, 'predicted' at 0.55-0.75
  confidence — the cascade input for step 2.

Small enough to load in <1s; rich enough to exercise every pattern in
all three steps: AS OF replay, polled context cascade, evidence-algebra
fusion across two distinct LLM sources plus a probabilistic classifier.
"""

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
    """Build the operational world model.

    data_dir=None  → in-memory (fast; AS OF replay still works within the
                     session but state vanishes on close).
    data_dir=path  → persistent on disk; WAL is durable, AS OF replay
                     works across process restarts. Step 1 (persistent
                     memory) needs this.
    """
    rng = random.Random(7)
    db = ArcFlow(data_dir) if data_dir else ArcFlow()

    # --- Symbols + day-zero fundamentals (observed, bulk-loaded) ----------
    # Bulk ingest bypasses the WAL — cold history that we never need to
    # replay seq-by-seq. Decisions and revisions enter through execute()
    # later so the WAL stays a clean log of *what changed*, not fixture
    # noise.
    symbol_nodes = db.bulk_create_nodes([
        (["Symbol"], {
            "ticker": tkr,
            "sector": sec,
            "init_close": init,
            "_observation_class": "observed",
            "_confidence": 1.00,
            "_source": "reference_data_v1",
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
            "revision": "original",
            "_observation_class": "observed",
            "_confidence": 1.00,
            "_source": "fundamentals_filing_v1",
        })
        for tkr, _sec, _init in SYMBOLS
    ])
    db.bulk_create_relationships(
        "HAS_FUNDAMENTAL",
        [(by_ticker[SYMBOLS[i][0]], fnid, {})
         for i, fnid in enumerate(fund_nodes)],
    )

    # --- OHLCV bars — 8 symbols × 60 days = 480 nodes (observed) ----------
    bar_specs = []
    for tkr, sec, init_close in SYMBOLS:
        price = init_close
        for d in range(DAYS):
            shock = rng.gauss(0.0, init_close * 0.012)  # ~1.2 % daily vol
            price = max(1.0, price + shock)
            open_ = price * (1.0 + rng.uniform(-0.003, 0.003))
            high = max(price, open_) * (1.0 + rng.uniform(0.0, 0.005))
            low = min(price, open_) * (1.0 - rng.uniform(0.0, 0.005))
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
                "_observation_class": "observed",
                "_confidence": 0.99,
                "_source": "tape_v1",
            }))
    bar_nodes = db.bulk_create_nodes(bar_specs)

    bar_to_symbol = []
    for i, spec in enumerate(bar_specs):
        ticker = spec[1]["ticker"]
        bar_to_symbol.append((by_ticker[ticker], bar_nodes[i], {}))
    db.bulk_create_relationships("HAS_BAR", bar_to_symbol)

    # --- News sentiment — two distinct LLM sources (predicted) ------------
    # These are the kind of facts an LLM-driven harness emits constantly:
    # short-lived, low-to-mid confidence, model-tagged so the evidence
    # algebra can prefer observed signals when they disagree.
    sentiment_specs = [
        # (ticker, day, score, conf, topic, llm_source)
        ("TECH-01",  8, +0.42, 0.55, "earnings beat rumor",        "sentiment_llm_v1"),
        ("TECH-01", 22, -0.18, 0.40, "supply-chain article",       "sentiment_llm_v1"),
        ("TECH-03", 12, +0.61, 0.62, "product launch leak",        "sentiment_llm_v2"),
        ("ENGY-02", 30, +0.30, 0.45, "buyback chatter",            "sentiment_llm_v2"),
        ("ENGY-02", 38, -0.55, 0.70, "fraud investigation report", "sentiment_llm_v1"),
        ("HLTH-02", 44, +0.25, 0.50, "FDA decision speculation",   "sentiment_llm_v2"),
    ]
    news_nodes = db.bulk_create_nodes([
        (["NewsSentiment"], {
            "ticker": tkr,
            "day_idx": day,
            "score": score,
            "_confidence": conf,
            "_observation_class": "predicted",
            "_source": llm_source,
            "headline_topic": topic,
        })
        for tkr, day, score, conf, topic, llm_source in sentiment_specs
    ])
    db.bulk_create_relationships(
        "MENTIONS",
        [(by_ticker[s[0]], news_nodes[i], {})
         for i, s in enumerate(sentiment_specs)],
    )

    # --- Regime classifications — HMM (predicted) -------------------------
    # The regime classifier emits one belief per symbol every 15 days,
    # representing "this is what the market state looks like right now."
    # It's predicted, not observed — even when accuracy is high, you treat
    # the output as a forward-looking model belief.
    regime_specs = []
    regimes = ["trending", "mean_reverting", "high_vol", "low_vol"]
    for tkr, _sec, _init in SYMBOLS:
        for d in [15, 30, 45, 55]:
            regime_specs.append((["RegimeBelief"], {
                "ticker": tkr,
                "day_idx": d,
                "regime": regimes[rng.randrange(4)],
                "_observation_class": "predicted",
                "_confidence": round(rng.uniform(0.55, 0.75), 2),
                "_source": "regime_hmm_v1",
            }))
    regime_nodes = db.bulk_create_nodes(regime_specs)
    db.bulk_create_relationships(
        "REGIME_FOR",
        [(by_ticker[regime_specs[i][1]["ticker"]], rnid, {})
         for i, rnid in enumerate(regime_nodes)],
    )

    return db, by_ticker


def stats(db):
    out = {}
    for label, q in [
        ("symbols",        "MATCH (s:Symbol) RETURN count(*) AS n"),
        ("fundamentals",   "MATCH (f:Fundamental) RETURN count(*) AS n"),
        ("bars",           "MATCH (b:DailyBar) RETURN count(*) AS n"),
        ("news",           "MATCH (n:NewsSentiment) RETURN count(*) AS n"),
        ("regime_beliefs", "MATCH (r:RegimeBelief) RETURN count(*) AS n"),
    ]:
        rows = list(db.execute(q))
        out[label] = int(rows[0]["n"])
    return out


if __name__ == "__main__":
    db, _ = make_db()
    print("operational world model loaded:")
    for k, v in stats(db).items():
        print(f"  {k:18s}  {v:,}")
    db.close()
