"""
Step 3 — Evidence-algebra fusion: one MATCH shape, every trust tier.

The pattern that lets a trading agent reason across heterogeneous signals
without schema-drift hell:

    Modern algo-trading harnesses fuse at least four signal classes —
    technical (deterministic, observed at high confidence), fundamental
    (less frequent, anchored to a revision), sentiment (LLM-emitted, low
    confidence, occasionally wrong), and regime beliefs (probabilistic
    HMM output, mid confidence). The naive shape needs four tables, four
    schemas, four JOIN paths, four "which confidence column was this
    again?" code paths.

In ArcFlow's operational world model, every fact carries the same two
properties:

    _observation_class ∈ {'observed', 'inferred', 'predicted'}
    _confidence        ∈ [0.0, 1.0]

(See /concepts/world-model — the research community is publishing papers
on "calibrated uncertainty in neural world models." ArcFlow has had
calibrated uncertainty as a day-one data-model commitment.)

This is the *evidence algebra*: one filter predicate, one ranking
expression, one trust-tier knob. Agreement, disagreement, and confidence
filtering all share the same MATCH shape — swapping the predicate is the
entire delta.

What this step demonstrates:

    1. Write inferred facts back into the world model.
       Compute 20-day momentum via a window function; persist the result
       as `Signal` nodes tagged `_observation_class='observed'` (these
       are deterministic derivations from observed prices, so 0.95 conf).
    2. Fusion query — agreement.
       Technical momentum + LLM sentiment pointing the same direction.
       Fused score weights each by its own confidence.
    3. Same shape — disagreement.
       Same MATCH, opposite predicate. Surfaces the trades worth a human
       eyeball.
    4. Same shape — regime context layered in.
       Add a third source (HMM regime belief) without touching the query
       structure. The world model absorbs new signal types without
       schema migration.
    5. Same shape — trust-tier filter.
       "Only feed the LLM facts with confidence ≥ 0.6" is one predicate
       change.

The whole point: in the operational world model the SAME query language
spans every trust tier. The agent stops being a babysitter for schema
glue and starts being an agent.
"""

import shutil
import tempfile

from _load import make_db


def main():
    data_dir = tempfile.mkdtemp(prefix="arcflow-algo-trading-")
    db, by_ticker = make_db(data_dir)

    # ---- 1. Compute technical signals + write back as observed facts ----
    # Momentum signal: 20-day return. Computed via a window function,
    # persisted as Signal nodes tagged `_observation_class='observed'`
    # at high confidence — these are deterministic derivations from
    # observed prices.
    #
    # WorldCypher targets GQL, where the intermediate-pipe step is
    # `RETURN x NEXT` (not Cypher's `WITH`). NULL handling for the
    # first 20 rows per symbol lives in Python.
    signal_rows = list(db.execute("""
        MATCH (b:DailyBar)
        RETURN b.ticker AS ticker,
               b.day_idx AS day_idx,
               b.close AS close,
               lag(b.close, 20) OVER (
                   PARTITION BY b.ticker ORDER BY b.day_idx
               ) AS close_20d_ago
    """))
    signal_rows = [r for r in signal_rows if r["close_20d_ago"] is not None]
    print(f"Computed {len(signal_rows)} momentum observations via window function")

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
            "_source": "ohlcv_pipeline_v1",
        }))
    sig_nodes = db.bulk_create_nodes(sig_specs)
    db.bulk_create_relationships(
        "EMITS",
        [(by_ticker[spec[1]["ticker"]], sig_nodes[i], {})
         for i, spec in enumerate(sig_specs)],
    )

    # ---- 2. Fusion: agreement between technical and sentiment ----
    # One MATCH, two relationship traversals. Each signal carries its
    # own _confidence; the fused score is a confidence-weighted sum.
    print("\n--- AGREEMENT: technical momentum AND sentiment lean the same way ---")
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
               news._source AS sent_source,
               news.headline_topic AS topic,
               sig.score * sig._confidence
                 + news.score * news._confidence AS fused_score
        ORDER BY fused_score DESC
    """):
        print(f"  {dict(r)}")

    # ---- 3. Same shape: disagreement worth a human eyeball ----
    print("\n--- DISAGREEMENT: technical vs sentiment point opposite ways ---")
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
               news._source AS sent_source,
               news.headline_topic AS topic
        ORDER BY day
    """):
        print(f"  {dict(r)}")

    # ---- 4. Same shape: layer in HMM regime beliefs as a third source ----
    # The regime classifier emits one belief every 15 days. This query
    # finds days where technical momentum was strong AND the regime was
    # 'trending' — high-conviction setups across two independent sources,
    # neither of which is the news LLM.
    print("\n--- THREE-SOURCE CROSS-CHECK: strong momentum + 'trending' regime ---")
    for r in db.execute("""
        MATCH (s:Symbol)-[:EMITS]->(sig:Signal),
              (s)-[:REGIME_FOR]->(reg:RegimeBelief)
        WHERE sig.day_idx = reg.day_idx
          AND reg.regime = 'trending'
          AND sig.score > 0.03
        RETURN s.ticker AS ticker,
               sig.day_idx AS day,
               sig.score AS mom_20d,
               reg.regime AS regime,
               reg._confidence AS regime_conf,
               reg._source AS regime_source
        ORDER BY sig.score DESC
    """):
        print(f"  {dict(r)}")

    # ---- 5. Same shape: trust-tier filter for the agent's prompt ----
    # "Only feed the LLM facts with confidence ≥ 0.6." One predicate.
    print("\n--- TRUST TIER: high-confidence signal counts by ticker ---")
    for r in db.execute("""
        MATCH (s:Symbol)-[:EMITS]->(sig:Signal)
        WHERE sig._confidence >= 0.6
        RETURN s.ticker AS ticker, count(sig) AS high_conf_signals
        ORDER BY ticker
    """):
        print(f"  {dict(r)}")

    print("\n--- TRUST TIER: high-confidence news by ticker ---")
    for r in db.execute("""
        MATCH (s:Symbol)-[:MENTIONS]->(news:NewsSentiment)
        WHERE news._confidence >= 0.6
        RETURN s.ticker AS ticker, count(news) AS high_conf_news
        ORDER BY ticker
    """):
        print(f"  {dict(r)}")

    print("\n--- What this proves ---")
    print("  - Technical, sentiment, and HMM-regime signals live in ONE graph,")
    print("    distinguished by `_observation_class` and weighted by `_confidence`.")
    print("    No schema drift, no JOIN chain across silos.")
    print("  - Agreement / disagreement / three-source / trust-tier — all share the")
    print("    SAME MATCH shape. Swapping a single predicate is the entire delta.")
    print("  - When the LLM tier adds a new signal source tomorrow (analyst-call")
    print("    extraction, satellite-imagery scores, options-flow detection), it")
    print("    writes `_observation_class='predicted'` facts into the same graph.")
    print("    Every existing fusion query absorbs it automatically.")
    print("  - The evidence algebra IS the calibrated-uncertainty primitive the")
    print("    research community is publishing papers about. In the operational")
    print("    world model it is the data model itself, not a feature on top.")

    db.close()
    shutil.rmtree(data_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
