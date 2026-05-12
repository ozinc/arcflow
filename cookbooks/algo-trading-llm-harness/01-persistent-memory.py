"""
Step 1 — Persistent memory for an LLM trading agent.

The pattern: an LLM-driven strategy decided at day 34 to take a position in
ENGY-02 based on the fundamentals visible at that moment. On day 35, ENGY-02
restates its earnings (a real-world look-ahead-bias landmine). The strategy
must be able to ask, *deterministically*: "what fundamentals did I see when
I decided?" — not "what do they look like now?"

ArcFlow provides this with two primitives, both shipped:

1. The two-tier ingest API. Bulk loaders (`bulk_create_nodes` /
   `bulk_create_relationships`) bypass the WAL — perfect for cold history
   that will never be replayed seq-by-seq. `execute()` mutations are
   WAL-journaled, one monotonic seq per `execute()` call. Splitting a
   restatement into two `execute()` calls (eps update, then revision
   flag) gives the auditor a staged trail; comma-`SET` within a single
   statement is atomic and gets one seq. The decision boundary between
   "fixture data" and "auditable decision" is a single API choice.

2. `MATCH ... AS OF seq $param ... RETURN ...` — replay the graph at any
   past seq. Bit-for-bit reproducible. No interpolation, no estimation.

Run with `_load.py` for the fixture; this step adds the restatement and the
trade decision via `execute()` so they enter the WAL.
"""

import shutil
import tempfile

from _load import make_db


def main():
    # AS OF seq requires a persistent ArcFlow instance.
    data_dir = tempfile.mkdtemp(prefix="arcflow-algo-trading-")
    db, by_ticker = make_db(data_dir)

    # --- WAL seq 1: the agent records its decision on day 34 ---
    db.execute("""
        CREATE (t:TradeDecision {
            ticker: 'ENGY-02',
            day_idx: 34,
            action: 'BUY',
            size: 5000,
            rationale: 'eps surprise, sector dispersion low',
            confidence: 0.78
        })
    """)
    print("seq 1: BUY decision recorded for ENGY-02 at day 34")

    # --- WAL seqs 2, 3: the fundamentals restatement on day 35 ---
    # Each execute() call gets one monotonic seq. We split the restatement
    # into two statements deliberately: AS OF seq 1 sees the original eps;
    # AS OF seq 2 sees the new eps but the old revision flag (a moment the
    # auditor cares about — the engineer applied the number before flipping
    # the audit flag); AS OF seq 3 sees both updated.
    db.execute("""
        MATCH (s:Symbol {ticker: 'ENGY-02'})-[:HAS_FUNDAMENTAL]->(f:Fundamental)
        SET f.eps = 2.10
    """)
    print("seq 2: ENGY-02 eps restated → 2.10")
    db.execute("""
        MATCH (s:Symbol {ticker: 'ENGY-02'})-[:HAS_FUNDAMENTAL]->(f:Fundamental)
        SET f.revision = 'restated-day-35'
    """)
    print("seq 3: ENGY-02 revision flag flipped → restated-day-35")

    # --- WAL seq 4: a second decision after the restatement ---
    db.execute("""
        CREATE (t:TradeDecision {
            ticker: 'ENGY-02',
            day_idx: 36,
            action: 'CLOSE',
            size: -5000,
            rationale: 'fundamentals revision invalidates thesis',
            confidence: 0.85
        })
    """)
    print("seq 4: CLOSE decision recorded for ENGY-02 at day 36")

    # ---- The agent asks: "what did I see when I made each decision?" ----
    fund_q = (
        "MATCH (s:Symbol {ticker: 'ENGY-02'})-[:HAS_FUNDAMENTAL]->(f:Fundamental) "
        "AS OF seq $s RETURN f.eps AS eps, f.revision AS revision"
    )
    decision_q = (
        "MATCH (t:TradeDecision {ticker: 'ENGY-02'}) "
        "AS OF seq $s RETURN t.day_idx AS day, t.action AS action, t.rationale AS why"
    )

    for seq, label in [
        (1, "BUY decision time — original fundamentals"),
        (2, "after eps restatement, before revision flag"),
        (3, "after both restatement assignments — full revision visible"),
        (4, "CLOSE decision time"),
    ]:
        print(f"\nAS OF seq {seq} ({label}):")
        for r in db.execute(fund_q, params={"s": seq}):
            print(f"  Fundamental: {dict(r)}")
        for r in db.execute(decision_q, params={"s": seq}):
            print(f"  Decision:    {dict(r)}")

    print("\nObservations:")
    print("  - The BUY at seq 1 was made against the ORIGINAL eps. No look-ahead.")
    print("  - The CLOSE at seq 4 was made against the RESTATED eps.")
    print("  - Replaying AS OF seq 1 is bit-for-bit what the agent saw at decision time.")
    print("  - The restatement landed as two seqs (one per execute()) — auditors can step")
    print("    through the eps change separately from the audit-flag flip.")
    print("  - The 480-bar cold history was bulk-loaded (no WAL entries) so the WAL is")
    print("    a clean log of *decisions and revisions only*, not fixture noise.")

    db.close()
    shutil.rmtree(data_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
