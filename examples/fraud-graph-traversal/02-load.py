"""Step 02 — Load data/transfers.parquet into ArcFlow.

Run:
    uv run python 02-load.py
"""
from __future__ import annotations

import time

from _load import load


def main() -> None:
    t0 = time.perf_counter()
    db, rows = load(verbose=True)
    elapsed = time.perf_counter() - t0
    print(f"loaded in {elapsed:.2f}s ({len(rows) / elapsed:.0f} transfers/sec)")

    n_accts = db.execute("MATCH (a:Account) RETURN count(a)").get(0, 0)
    n_xfer = db.execute("MATCH (t:Transfer) RETURN count(t)").get(0, 0)
    n_sent = db.execute("MATCH ()-[r:SENT]->() RETURN count(r)").get(0, 0)
    n_to = db.execute("MATCH ()-[r:TO]->() RETURN count(r)").get(0, 0)

    print(
        f"in-graph: accounts={n_accts}, transfers={n_xfer}, "
        f"SENT edges={n_sent}, TO edges={n_to}"
    )
    db.close()
    print("OK")


if __name__ == "__main__":
    main()
