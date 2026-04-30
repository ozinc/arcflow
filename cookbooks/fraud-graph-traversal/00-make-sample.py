"""Synthesize the bank-transfer Parquet file used by subsequent steps.

50 accounts, 220 transfers across 14 days. Three fraud patterns are
planted alongside ~180 normal background transfers:

  MULE-1     receives from 12 distinct accounts (fan-in concentration)
  SPLITTER-1 sends to 9 distinct recipients (fan-out layering)
  LAYER-A → LAYER-B → LAYER-C → LAYER-D — 4-hop chain, each leg ~$9,500

Output:
    data/transfers.parquet  (~12 KB)

Schema:
    transfer_id   str        unique id like "TR-00042"
    src_acct      str
    dst_acct      str
    amount        float64    USD
    timestamp     float64    seconds since epoch start

Deterministic — same seed → byte-equal output, so CI snapshots stay stable.
"""
from __future__ import annotations

import random
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


def main() -> None:
    rng = random.Random(20260430)
    out = Path(__file__).parent / "data" / "transfers.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)

    accounts = [f"A{n:03d}" for n in range(40)] + [
        "MULE-1",
        "SPLITTER-1",
        "LAYER-A",
        "LAYER-B",
        "LAYER-C",
        "LAYER-D",
        "VICTIM-1",
        "DUMMY-1",
        "DUMMY-2",
        "DUMMY-3",
    ]
    rows = {
        "transfer_id": [],
        "src_acct": [],
        "dst_acct": [],
        "amount": [],
        "timestamp": [],
    }
    next_id = 1

    def add(src: str, dst: str, amount: float, ts: float) -> None:
        nonlocal next_id
        rows["transfer_id"].append(f"TR-{next_id:05d}")
        rows["src_acct"].append(src)
        rows["dst_acct"].append(dst)
        rows["amount"].append(round(amount, 2))
        rows["timestamp"].append(round(ts, 4))
        next_id += 1

    # Background — random low-value transfers between random accounts.
    for _ in range(180):
        src = rng.choice(accounts[:40])
        dst = rng.choice([a for a in accounts[:40] if a != src])
        amount = rng.uniform(50.0, 2000.0)
        ts = rng.uniform(0.0, 14 * 86400)
        add(src, dst, amount, ts)

    # MULE-1: fan-in from 12 distinct sources.
    sources = rng.sample(accounts[:40], 12)
    for src in sources:
        amount = rng.uniform(800.0, 1500.0)
        ts = rng.uniform(7 * 86400, 9 * 86400)
        add(src, "MULE-1", amount, ts)

    # SPLITTER-1: fan-out to 9 distinct recipients (layering).
    recipients = rng.sample(accounts[:40], 9)
    for dst in recipients:
        amount = rng.uniform(900.0, 1100.0)
        ts = rng.uniform(10 * 86400, 11 * 86400)
        add("SPLITTER-1", dst, amount, ts)

    # LAYER chain: VICTIM-1 → LAYER-A → B → C → D, each leg ~$9,500.
    base = 9500.0
    chain = ["VICTIM-1", "LAYER-A", "LAYER-B", "LAYER-C", "LAYER-D"]
    t = 12 * 86400
    for src, dst in zip(chain, chain[1:]):
        leg = base + rng.gauss(0, 50.0)
        add(src, dst, leg, t)
        t += rng.uniform(60.0, 600.0)

    # Sort by transfer_id so output is stable.
    order = sorted(range(len(rows["transfer_id"])), key=lambda i: rows["transfer_id"][i])
    sorted_rows = {k: [v[i] for i in order] for k, v in rows.items()}

    table = pa.table(
        sorted_rows,
        schema=pa.schema(
            [
                ("transfer_id", pa.string()),
                ("src_acct", pa.string()),
                ("dst_acct", pa.string()),
                ("amount", pa.float64()),
                ("timestamp", pa.float64()),
            ]
        ),
    )

    pq.write_table(table, out, compression="snappy")
    size_kb = out.stat().st_size / 1024
    print(
        f"wrote {out} ({len(sorted_rows['transfer_id'])} transfers, "
        f"{size_kb:.1f} KB)"
    )


if __name__ == "__main__":
    main()
