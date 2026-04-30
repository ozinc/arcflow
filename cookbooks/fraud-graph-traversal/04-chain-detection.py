"""Step 04 — Multi-hop value-conserving chain detection.

The query: find 4-hop chains A → B → C → D → E where each leg moves an
amount in [LEG_MIN, LEG_MAX]. This is the layering pattern — same money
walked through multiple intermediaries.

Why two-stage: WorldCypher 1.6.6 plans the 4-hop traversal cleanly, but
applying a WHERE predicate to multiple deeply-bound Transfer nodes in a
single MATCH is not yet stable. We let the engine enumerate chains, then
filter the rows in Python. The same recipe drops to a one-MATCH query
once that engine wave ships.

Run:
    uv run python 04-chain-detection.py
"""
from __future__ import annotations

from _load import load

LEG_MIN = 9000.0
LEG_MAX = 10000.0


def main() -> None:
    db, _ = load()

    print(
        f"\n[1] 4-hop value-conserving chains "
        f"(each leg in [${LEG_MIN:,.0f}, ${LEG_MAX:,.0f}]):"
    )

    q = (
        "MATCH (a:Account)-[:SENT]->(t1:Transfer)-[:TO]->(b:Account)"
        "      -[:SENT]->(t2:Transfer)-[:TO]->(c:Account)"
        "      -[:SENT]->(t3:Transfer)-[:TO]->(d:Account)"
        "      -[:SENT]->(t4:Transfer)-[:TO]->(e:Account) "
        "RETURN a.acct_id AS a, b.acct_id AS b, c.acct_id AS c, "
        "       d.acct_id AS d, e.acct_id AS e, "
        "       t1.amount AS leg1, t2.amount AS leg2, "
        "       t3.amount AS leg3, t4.amount AS leg4"
    )
    chains = []
    for row in db.execute(q):
        legs = [float(row[f"leg{i}"]) for i in (1, 2, 3, 4)]
        if all(LEG_MIN <= leg <= LEG_MAX for leg in legs):
            chains.append((row, legs))

    print(f"    {len(chains)} chain(s) match the value-conserving filter")
    for row, legs in chains:
        print(
            f"    {row['a']:>10} -> {row['b']:>10} -> {row['c']:>10} "
            f"-> {row['d']:>10} -> {row['e']:>10}"
        )
        print(
            f"      legs: ${legs[0]:>8,.2f}  ${legs[1]:>8,.2f}  "
            f"${legs[2]:>8,.2f}  ${legs[3]:>8,.2f}"
        )

    # 2-hop drill-down on MULE-1 — uses single-WHERE so the engine handles
    # the predicate end to end.
    print(f"\n[2] 2-hop chains touching MULE-1 (drill into the mule):")
    q2 = (
        "MATCH (src:Account)-[:SENT]->(:Transfer)-[:TO]->(m:Account)"
        "      -[:SENT]->(t:Transfer)-[:TO]->(dst:Account) "
        "WHERE m.acct_id = 'MULE-1' "
        "RETURN src.acct_id AS src, dst.acct_id AS dst, t.amount AS forwarded "
        "ORDER BY t.amount DESC "
        "LIMIT 5"
    )
    rows = list(db.execute(q2))
    if not rows:
        print("    no onward forwarding from MULE-1 in this window")
    else:
        for row in rows:
            print(
                f"    {row['src']} -> MULE-1 -> {row['dst']}  "
                f"(forwarded ${float(row['forwarded']):,.2f})"
            )

    db.close()
    print("\nOK")


if __name__ == "__main__":
    main()
