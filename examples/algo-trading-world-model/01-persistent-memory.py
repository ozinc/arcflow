"""
Step 1 — Persistent memory: the world model remembers what the agent saw.

The pattern that makes algorithmic trading audits possible (and that 99%
of "AI trading harness" stacks get wrong):

    An LLM-driven strategy decided to BUY ENGY-02 at day 34, reasoning
    from the fundamentals visible at that moment. The next day, ENGY-02
    restates its earnings — eps drops 60%, the audit flag flips.

    Six weeks later, post-mortem: did the agent commit a fineable
    look-ahead-bias error, or was the BUY justified given what was
    knowable at the time?

In a typical stack the answer is "we don't know" — the database has only
the *current* fundamentals; the old ones are gone. The agent's decision
trail is in a separate log. Reconstructing what the agent saw requires
correlating three half-evidence sources and accepting fuzzy answers.

In ArcFlow's operational world model the answer is one query:

    MATCH (s:Symbol {ticker:'ENGY-02'})-[:HAS_FUNDAMENTAL]->(f)
    AS OF seq 1
    RETURN f.eps, f.revision

Bit-for-bit what the agent saw before the restatement entered the WAL.
No interpolation, no estimation, no separate audit log to correlate.

Two engine primitives make this work:

1. Two-tier ingest as the auditability boundary.
   `bulk_create_nodes` / `bulk_create_relationships` bypass the WAL —
   perfect for cold history that never needs seq-by-seq replay.
   `execute()` mutations are WAL-journaled, one monotonic seq per call.
   Splitting a multi-field restatement into multiple `execute()` calls
   gives the auditor a staged trail; keeping it as one comma-SET
   statement is atomic and gets one seq.

2. `MATCH ... AS OF seq $param ... RETURN ...` replays the graph at any
   past seq. Same query language, same params surface, just one extra
   keyword. The agent's decisions land in the same world model as the
   evidence it used — auditing becomes data, not detective work.

Run `_load.py` first for the fixture (cold history bulk-loaded, zero WAL
entries). This step adds the agent's decision and the restatement via
`execute()`, producing a small, clean WAL where every entry has meaning.
"""

import shutil
import tempfile

from _load import make_db


def main():
    # AS OF seq requires a persistent ArcFlow instance.
    data_dir = tempfile.mkdtemp(prefix="arcflow-algo-trading-")
    db, _by_ticker = make_db(data_dir)

    # --- WAL seq 1: the agent records its BUY decision on day 34 ---------
    # The TradeDecision is itself a first-class world-model node — same
    # graph, same query language, same temporal versioning. The agent
    # doesn't "log" decisions to a sidecar; the decisions become part of
    # the world the next query can reason about.
    db.execute("""
        CREATE (t:TradeDecision {
            ticker: 'ENGY-02',
            day_idx: 34,
            action: 'BUY',
            size: 5000,
            rationale: 'eps surprise, sector dispersion low',
            confidence: 0.78,
            _observation_class: 'observed',
            _confidence: 1.00,
            _source: 'agent_v1'
        })
    """)
    print("seq 1: BUY decision recorded for ENGY-02 at day 34")

    # --- WAL seqs 2, 3: the fundamentals restatement on day 35 -----------
    # Each execute() call gets one monotonic seq. We split the restatement
    # into two statements deliberately so the AS OF replay can show three
    # distinct intermediate states (a moment the auditor cares about — the
    # engineer applied the new number before flipping the audit flag).
    db.execute("""
        MATCH (s:Symbol {ticker:'ENGY-02'})-[:HAS_FUNDAMENTAL]->(f:Fundamental)
        SET f.eps = 2.10
    """)
    print("seq 2: ENGY-02 eps restated → 2.10")
    db.execute("""
        MATCH (s:Symbol {ticker:'ENGY-02'})-[:HAS_FUNDAMENTAL]->(f:Fundamental)
        SET f.revision = 'restated-day-35'
    """)
    print("seq 3: ENGY-02 revision flag flipped → restated-day-35")

    # --- WAL seq 4: the agent's CLOSE decision after the restatement ------
    db.execute("""
        CREATE (t:TradeDecision {
            ticker: 'ENGY-02',
            day_idx: 36,
            action: 'CLOSE',
            size: -5000,
            rationale: 'fundamentals revision invalidates thesis',
            confidence: 0.85,
            _observation_class: 'observed',
            _confidence: 1.00,
            _source: 'agent_v1'
        })
    """)
    print("seq 4: CLOSE decision recorded for ENGY-02 at day 36")

    # ---- The audit query: "what did the agent see at each decision?" ----
    # Same query, AS OF different seqs. The world model has both the
    # fundamentals AND the decisions in one graph, replayable together.
    fund_q = (
        "MATCH (s:Symbol {ticker:'ENGY-02'})-[:HAS_FUNDAMENTAL]->(f:Fundamental) "
        "AS OF seq $s RETURN f.eps AS eps, f.revision AS revision"
    )
    decision_q = (
        "MATCH (t:TradeDecision {ticker:'ENGY-02'}) "
        "AS OF seq $s RETURN t.day_idx AS day, t.action AS action, t.rationale AS why"
    )

    print("\n--- Operational world model — AS OF seq replay ---")
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

    print("\n--- What this proves ---")
    print("  - The BUY at seq 1 was made against the ORIGINAL eps. No look-ahead.")
    print("  - The CLOSE at seq 4 was made against the RESTATED eps.")
    print("  - The 480-bar cold history was bulk-loaded (no WAL entries),")
    print("    so the WAL is a clean log of *decisions and revisions only*,")
    print("    not fixture noise. Every seq in the WAL is meaningful.")
    print("  - Decisions and evidence are in the same graph, queried the")
    print("    same way. The audit trail IS the dataset a causal-inference")
    print("    model would want — there is no separate log to correlate.")

    db.close()
    shutil.rmtree(data_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
