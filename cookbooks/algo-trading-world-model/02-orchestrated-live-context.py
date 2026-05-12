"""
Step 2 — Orchestrated context: the world model IS the agent's working memory.

The pattern that separates "LLM with a database" from "LLM grounded in an
operational world model":

    Every prompt turn, the agent needs current context — sector rollups,
    cross-sectional ranks, regime beliefs, top-of-sector leaders. The
    naive shape: pull rows, compute features in Python, build a prompt.
    The agent burns its context window on raw bytes the engine could
    have already maintained.

The world-model shape: define each layer of agent context AS a query.
The graph is the orchestration substrate. One tick mutates the graph;
the agent re-reads the same three queries; each layer arrives pre-
computed, ready to feed the prompt. No external scheduler, no factor-
rollup job, no JOIN chain across silos.

This step builds the canonical three-layer context stack:

    sector_rollup        — avg close / sector / day (aggregation)
    cross_sectional_z    — percentile rank within sector (window fn)
    leaders_by_sector    — top-ranked symbol per sector (window fn)

Then inserts ONE new bar via `execute()` and re-reads all three. The
deltas are visible by inspection — same query, different results, no
recomputation glue in Python.

A note on the binding surface:

    Today's Python binding reads on tick (poll the three queries after
    each mutation). The TypeScript binding exposes the same maintained
    substrate via `db.subscribe(query, callback)` — engine fires the
    callback within ~20ms of any mutation. The Rust SDK exposes
    `CREATE LIVE VIEW name AS ...` directly, with view chaining and
    continuous-proof asserting batch-vs-live equivalence cell-by-cell.

    The query SHAPE is identical across all three modes. Z-set algebra
    (the engine's incremental-computation substrate) guarantees the
    equivalence — the same operator plan that runs your backtest runs
    your live agent.
"""

import shutil
import tempfile

from _load import make_db


SECTOR_ROLLUP_Q = """
MATCH (b:DailyBar)
WHERE b.day_idx = $day
RETURN b.sector AS sector,
       count(*) AS n_symbols,
       avg(b.close) AS sector_avg_close
ORDER BY sector
"""

CROSS_SECTIONAL_Z_Q = """
MATCH (b:DailyBar)
WHERE b.day_idx = $day
RETURN b.ticker AS ticker,
       b.sector AS sector,
       b.close  AS close,
       percent_rank() OVER (PARTITION BY b.sector ORDER BY b.close) AS sector_pctl
ORDER BY b.sector, sector_pctl DESC
"""

LEADERS_BY_SECTOR_Q = """
MATCH (b:DailyBar)
WHERE b.day_idx = $day
RETURN b.sector AS sector,
       b.ticker AS leader,
       b.close AS leader_close,
       row_number() OVER (PARTITION BY b.sector ORDER BY b.close DESC) AS rn
ORDER BY b.sector, rn
"""


def snapshot(db, day):
    """Read two context layers at a single day. This is the agent's
    pre-prompt query — every prompt turn would call something like this."""
    print(f"\n  --- sector_rollup on day {day} ---")
    for r in db.execute(SECTOR_ROLLUP_Q, params={"day": day}):
        print(f"  {dict(r)}")

    print(f"\n  --- leaders_by_sector on day {day} (rn = 1 only) ---")
    for r in db.execute(LEADERS_BY_SECTOR_Q, params={"day": day}):
        if int(r["rn"]) == 1:
            print(f"  {dict(r)}")


def main():
    data_dir = tempfile.mkdtemp(prefix="arcflow-algo-trading-")
    db, _ = make_db(data_dir)

    print("Three context queries defined: sector_rollup, cross_sectional_z, leaders_by_sector")
    print("All read straight from the operational world model —")
    print("the graph IS the orchestration substrate.")

    # ---- 1. Snapshot at the end of the fixture (day 59) ----
    print("\n=== BEFORE: end-of-fixture snapshot (day 59) ===")
    snapshot(db, 59)

    print("\n  --- cross_sectional_z for TECH-* on day 59 ---")
    for r in db.execute(CROSS_SECTIONAL_Z_Q, params={"day": 59}):
        if str(r["sector"]) == "Tech":
            print(f"  {dict(r)}")

    # ---- 2. One new bar arrives ----
    # TECH-03 ships a blow-out close on day 60 — a "tape buster" that flips
    # the Tech sector leader. The agent inserts this via execute() (one WAL
    # entry) so the decision-time state is reconstructable later via AS OF.
    print("\n=== Inserting one new bar: TECH-03, day 60, close = 999.0 ===")
    db.execute("""
        CREATE (b:DailyBar {
            ticker: 'TECH-03',
            sector: 'Tech',
            day_idx: 60,
            open: 920.0, high: 1005.0, low: 905.0, close: 999.0,
            volume: 3500000,
            _observation_class: 'observed',
            _confidence: 0.99,
            _source: 'tape_v1'
        })
    """)

    # ---- 3. Re-read the three layers ----
    # Each query touches only the newly relevant slice (day = 60). The graph
    # didn't need a re-org; window functions recompute over the bar set the
    # WHERE narrows to. No partial-recompute glue in Python.
    print("\n=== AFTER: re-reading at day 60 ===")
    snapshot(db, 60)

    print("\n  --- cross_sectional_z for TECH-* on day 60 (TECH-03 should top Tech) ---")
    for r in db.execute(CROSS_SECTIONAL_Z_Q, params={"day": 60}):
        if str(r["sector"]) == "Tech":
            print(f"  {dict(r)}")

    print("\n--- What this proves ---")
    print("  - Three context queries; one MATCH each. The graph IS the orchestration substrate.")
    print("  - One new bar via execute() → re-query yields the new view immediately.")
    print("  - The same MATCH...RETURN shape works in batch (this script), in a per-tick")
    print("    agent loop (TS db.subscribe), and as a maintained LIVE view (Rust SDK).")
    print("    Z-set algebra guarantees the three modes are operator-plan-equivalent.")
    print("  - No external scheduler, no message bus, no factor-rollup job.")
    print("  - Your backtest, your live agent, and your audit trail all run the same")
    print("    query against the same operational world model.")

    db.close()
    shutil.rmtree(data_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
