"""
Step 3 — Confidence-weighted signal fusion.

The pattern: a modern algo-trading agent fuses at least three signal classes —
technical (deterministic, observed at high confidence), fundamental (less
frequent, anchored to a revision), and sentiment / news (often LLM-generated,
low confidence, occasionally wrong). The harness has to express *all three*
in one graph and let a query weight them.

ArcFlow uses two well-typed properties for this (proven in the
spatiotemporal-tactical-queries recipe):

  * `_observation_class` — one of `observed` / `inferred` / `predicted`
  * `_confidence`        — a float in [0, 1]

Technical signals here are tagged `observed` at 0.95. The synthesized news
sentiment events (in `_load.py`) are tagged `predicted` at 0.40-0.70 —
representing what an LLM/sentiment model would emit. The same query shape
expresses:

  * "high-conviction trades where multiple sources agree"
  * "cross-source disagreement worth a human eyeball"

No JOIN chains, no COALESCE, no separate "signals_table" + "news_table"
schema drift. One graph; one filter predicate; one ranking expression.
"""

import shutil
import tempfile

from _load import make_db


def main():
    data_dir = tempfile.mkdtemp(prefix="arcflow-algo-trading-")
    db, by_ticker = make_db(data_dir)

    # ---- 1. Compute technical signals + write as observed facts ----
    # Momentum signal: 20-day return. We compute via a window function and
    # write back as graph facts tagged `observed` so the fusion query can
    # treat them uniformly with the news sentiment facts already present.
    #
    # The window function `lag()` is in the RETURN clause directly (no WITH —
    # WorldCypher targets GQL, where the intermediate-pipe step is `RETURN x
    # NEXT`, not Cypher's `WITH`). NULL handling lives in Python.
    signal_rows = list(db.execute("""
        MATCH (b:DailyBar)
        RETURN b.ticker AS ticker,
               b.day_idx AS day_idx,
               b.close AS close,
               lag(b.close, 20) OVER (
                   PARTITION BY b.ticker ORDER BY b.day_idx
               ) AS close_20d_ago
    """))
    # The first 20 rows per symbol have NULL close_20d_ago — filter in Python.
    signal_rows = [r for r in signal_rows if r["close_20d_ago"] is not None]
    print(f"Computed {len(signal_rows)} momentum observations via window function")

    # Bulk-load the technical signals as observed facts (cold derived data,
    # no need to WAL each one separately).
    sig_specs = []
    for r in signal_rows:
        ret = float(r["close"]) / float(r["close_20d_ago"]) - 1.0
        sig_specs.append((["Signal"], {
            "ticker": r["ticker"],
            "day_idx": int(r["day_idx"]),
            "kind": "momentum_20d",
            "score": round(ret, 4),
            "_confidence": 0.95,
            "_observation_class": "observed",
            "source": "ohlcv_pipeline",
        }))
    sig_nodes = db.bulk_create_nodes(sig_specs)
    # Link each signal back to its Symbol so the fusion query can traverse.
    db.bulk_create_relationships(
        "EMITS",
        [(by_ticker[spec[1]["ticker"]], sig_nodes[i], {})
         for i, spec in enumerate(sig_specs)],
    )

    # ---- 2. Fusion query: high-conviction multi-source agreement ----
    # Find every (symbol, day) where BOTH a momentum signal AND a news
    # sentiment fact exist, and both lean the same direction. The
    # `_observation_class` filter keeps observed vs predicted explicit;
    # the `_confidence` is preserved on the edge so the agent can pick
    # its own threshold.
    print("\n--- Fusion: agreement between technical and sentiment ---")
    for r in db.execute("""
        MATCH (s:Symbol)-[:EMITS]->(sig:Signal),
              (s)-[:MENTIONS]->(news:NewsSentiment)
        WHERE sig.day_idx = news.day_idx
          AND sig.score * news.score > 0
        RETURN s.ticker AS ticker,
               sig.day_idx AS day,
               sig.score AS mom_20d,
               sig._confidence AS mom_conf,
               news.score AS sent_score,
               news._confidence AS sent_conf,
               news.headline_topic AS topic,
               sig.score * sig._confidence
                 + news.score * news._confidence AS fused_score
        ORDER BY fused_score DESC
    """):
        print(f"  {dict(r)}")

    # ---- 3. Same shape: cross-source disagreement worth investigating ----
    print("\n--- Disagreement: technical vs sentiment pointing different ways ---")
    for r in db.execute("""
        MATCH (s:Symbol)-[:EMITS]->(sig:Signal),
              (s)-[:MENTIONS]->(news:NewsSentiment)
        WHERE sig.day_idx = news.day_idx
          AND sig.score * news.score < 0
        RETURN s.ticker AS ticker,
               sig.day_idx AS day,
               sig.score AS mom_20d,
               news.score AS sent_score,
               news._confidence AS sent_conf,
               news.headline_topic AS topic
        ORDER BY day
    """):
        print(f"  {dict(r)}")

    # ---- 4. Same shape: trust-tier filter for the agent's prompt context ----
    # "Only feed the LLM facts with confidence ≥ 0.6." This is the same
    # `_confidence` predicate the spatiotemporal recipe uses — different
    # domain, identical shape.
    print("\n--- High-confidence signals (>= 0.6) by ticker ---")
    for r in db.execute("""
        MATCH (s:Symbol)-[:EMITS]->(sig:Signal)
        WHERE sig._confidence >= 0.6
        RETURN s.ticker AS ticker, count(sig) AS high_conf_signals
        ORDER BY ticker
    """):
        print(f"  {dict(r)}")

    print("\n--- High-confidence news (>= 0.6) by ticker ---")
    for r in db.execute("""
        MATCH (s:Symbol)-[:MENTIONS]->(news:NewsSentiment)
        WHERE news._confidence >= 0.6
        RETURN s.ticker AS ticker, count(news) AS high_conf_news
        ORDER BY ticker
    """):
        print(f"  {dict(r)}")

    print("\nObservations:")
    print("  - Technical signals and news sentiment live in ONE graph, distinguished by")
    print("    `_observation_class` and weighted by `_confidence`. No schema drift.")
    print("  - The fusion query is one MATCH with two relationship traversals — no JOINs.")
    print("  - The agreement / disagreement / trust-tier queries share the same shape;")
    print("    swapping the predicate is the entire delta.")
    print("  - An LLM-driven layer can append more `_observation_class=predicted` facts")
    print("    (rationales, alternate-scenarios, regime-classifications) and every existing")
    print("    fusion query automatically incorporates them — no schema migration.")

    db.close()
    shutil.rmtree(data_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
