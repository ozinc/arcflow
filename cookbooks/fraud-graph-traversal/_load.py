"""Shared loader used by every step that needs the graph in memory.

Each step opens a fresh in-memory ArcFlow database and re-loads from the
Parquet file. For 220 transfers this is well under one second.

Schema (see 01-fraud-patterns.md):
    (:Account {acct_id})
    (:Transfer {transfer_id, amount, timestamp})
    (:Account)-[:SENT]->(:Transfer)-[:TO]->(:Account)
"""
from __future__ import annotations

from pathlib import Path

import pyarrow.parquet as pq

from arcflow import ArcFlow

HERE = Path(__file__).parent
INPUT = HERE / "data" / "transfers.parquet"


def load(verbose: bool = False):
    if not INPUT.exists():
        raise SystemExit(f"Missing {INPUT}. Run 00-make-sample.py first.")

    table = pq.read_table(INPUT)
    rows = table.to_pylist()

    accounts = sorted({r["src_acct"] for r in rows} | {r["dst_acct"] for r in rows})

    db = ArcFlow()

    for aid in accounts:
        db.execute(f"CREATE (:Account {{acct_id: '{aid}'}})")

    for r in rows:
        db.execute(
            "CREATE (:Transfer {"
            f"transfer_id: '{r['transfer_id']}', "
            f"amount: {r['amount']}, timestamp: {r['timestamp']}"
            "})"
        )
        db.execute(
            "MATCH (a:Account {acct_id: '" + r["src_acct"] + "'}), "
            "(t:Transfer {transfer_id: '" + r["transfer_id"] + "'}) "
            "CREATE (a)-[:SENT]->(t)"
        )
        db.execute(
            "MATCH (t:Transfer {transfer_id: '" + r["transfer_id"] + "'}), "
            "(b:Account {acct_id: '" + r["dst_acct"] + "'}) "
            "CREATE (t)-[:TO]->(b)"
        )

    if verbose:
        print(f"loaded {len(rows)} transfers across {len(accounts)} accounts")

    return db, rows
