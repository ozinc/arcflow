"""Step 03 — Fan-in (mule) and fan-out (splitter) detection.

Pulls (src, dst) pairs from one MATCH and tallies distinct counterparts
per account in Python. The query side is trivial; the analysis side is
where business rules live (thresholds, time windows, account categories).

Why this shape — `count(DISTINCT x)` is not yet stable in WorldCypher 1.6.6,
so we keep the engine query simple and tally distincts client-side.
A future engine release flips this single step to a one-line aggregate;
the surrounding code stays as is.

Run:
    uv run python 03-fan-detection.py
"""
from __future__ import annotations

from collections import defaultdict

from _load import load

FAN_IN_THRESHOLD = 8
FAN_OUT_THRESHOLD = 8


def main() -> None:
    db, _ = load()

    result = db.execute(
        "MATCH (src:Account)-[:SENT]->(t:Transfer)-[:TO]->(dst:Account) "
        "RETURN src.acct_id AS src, dst.acct_id AS dst, t.amount AS amount"
    )
    pairs = [(row["src"], row["dst"], float(row["amount"])) for row in result]

    fan_in: dict[str, set[str]] = defaultdict(set)
    fan_out: dict[str, set[str]] = defaultdict(set)
    volume_in: dict[str, float] = defaultdict(float)
    volume_out: dict[str, float] = defaultdict(float)
    for src, dst, amount in pairs:
        fan_in[dst].add(src)
        fan_out[src].add(dst)
        volume_in[dst] += amount
        volume_out[src] += amount

    print("\n[1] Fan-in concentration — accounts receiving from many sources:")
    top_in = sorted(fan_in.items(), key=lambda kv: -len(kv[1]))[:5]
    for acct, sources in top_in:
        flag = "  <-- FLAG" if len(sources) >= FAN_IN_THRESHOLD else ""
        print(
            f"    {acct:>12}  distinct_sources={len(sources):>3}  "
            f"total=${volume_in[acct]:>10,.2f}{flag}"
        )

    print("\n[2] Fan-out layering — accounts sending to many destinations:")
    top_out = sorted(fan_out.items(), key=lambda kv: -len(kv[1]))[:5]
    for acct, dsts in top_out:
        flag = "  <-- FLAG" if len(dsts) >= FAN_OUT_THRESHOLD else ""
        print(
            f"    {acct:>12}  distinct_destinations={len(dsts):>3}  "
            f"total=${volume_out[acct]:>10,.2f}{flag}"
        )

    print(f"\n[3] Drill-down on planted patterns:")
    print(
        f"    MULE-1     received from {len(fan_in['MULE-1'])} distinct sources, "
        f"total=${volume_in['MULE-1']:,.2f}"
    )
    print(
        f"    SPLITTER-1 sent to        {len(fan_out['SPLITTER-1'])} distinct dsts,    "
        f"total=${volume_out['SPLITTER-1']:,.2f}"
    )

    db.close()
    print("\nOK")


if __name__ == "__main__":
    main()
