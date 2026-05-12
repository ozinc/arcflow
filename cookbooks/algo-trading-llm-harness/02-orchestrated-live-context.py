"""
Step 2 — Orchestrated context: the graph as the agent's pre-computed
working memory.

The pattern: an LLM agent shouldn't recompute "60-day rolling volatility for
every symbol, sector z-scores, top-of-sector ranks" inside the prompt. It
should READ that context, fresh, from a structure the engine maintains.

Today's Python binding accesses ArcFlow's maintained-query infrastructure
through *polling at the source tick* — the same pattern the
`multi-stream-spatiotemporal-world-model` recipe uses for 60-Hz tracking.
The TypeScript binding exposes `db.subscribe(query, callback)` directly;
the engine fires the callback within ~20 ms of any mutation. In Python the
equivalent is "execute the same query after each tick"; the cost is bounded
by query latency (well under the tick budget for an algo-trading loop).

The *important* part is the lesson: define each layer of agent context as
a query, and the GRAPH is the orchestration substrate. One mutation, three
re-queries; each layer is a single MATCH. No external scheduler, no message
bus, no JOIN chain across silos.

This step builds the canonical agent-context stack:

    sector_rollup       (avg close / sector / day — bar aggregation)
    cross_sectional_z   (per-day percentile rank of close within sector)
    leaders_by_sector   (top-ranked symbol per sector per day)

Then inserts ONE new bar via `execute()` and re-reads all three. The deltas
are visible by inspection — same query, different results, no recomputation
glue in Python.
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
    """Read all three context layers at a single day. This is the agent's
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
    print("All read straight from the graph — the maintained substrate IS the orchestration layer.")

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
    # entry) so the decision-time state is reconstructable later.
    print("\n=== Inserting one new bar: TECH-03, day 60, close = 999.0 ===")
    db.execute("""
        CREATE (b:DailyBar {
            ticker: 'TECH-03',
            sector: 'Tech',
            day_idx: 60,
            open: 920.0, high: 1005.0, low: 905.0, close: 999.0,
            volume: 3500000
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

    print("\nObservations:")
    print("  - Three context queries; one MATCH each. The graph is the orchestration substrate.")
    print("  - One new bar via execute() → re-query yields the new view immediately.")
    print("  - Python today reads on tick (polling); TypeScript exposes the same maintained")
    print("    state via db.subscribe(query, callback) — engine fires within ~20 ms.")
    print("  - No external scheduler, no message bus, no factor-rollup job.")
    print("  - The same MATCH ... RETURN shape works in batch and in the per-tick agent loop;")
    print("    Z-set algebra (PAT-0021) guarantees the equivalence inside the engine.")

    db.close()
    shutil.rmtree(data_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
