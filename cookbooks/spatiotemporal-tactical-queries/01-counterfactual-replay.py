"""
Counterfactual replay: "What did the world model show when the decision was made?"

Pattern: each `execute()` mutation advances the WAL by exactly one seq.
`AS OF seq <param>` takes the world model back to that point —
deterministic, not interpolated.

Two-tier API note: the bulk fast path (`bulk_create_nodes` /
`bulk_create_relationships`) is **current-state only** — it bypasses the
WAL for ingest throughput. Only `execute()` mutations enter the WAL and
become AS-OF replayable. Use bulk for fixture / historical data; use
`execute()` for decisions and observations you want auditable.

Engine quirk to know about (today, on 1.6.7): `walSeq()` in Cypher returns
the store's mutation counter (which advances on bulk_create too), not
the WAL's current seq. To pick a valid AS OF seq, count your `execute()`
mutations in your application — that's the WAL's seq space exactly.

This recipe deliberately uses an `execute()`-only workflow so the AS OF
replay path is clean. See `known-issues.mdx` for the interaction
between bulk_create_* and AS OF that you'll want to be aware of for
mixed workflows.

This script:
1. Records a decision via `execute()` → WAL seq 1.
2. Overturns the decision via comma-separated SET (one WAL entry per
   property assignment) → WAL seqs 2, 3.
3. Replays AS OF seq 1, 2, 3 to see the world model evolve.
"""

import shutil
import tempfile

from arcflow import ArcFlow


def main():
    # AS OF seq requires a WAL — only persistent (data_dir) instances have one.
    data_dir = tempfile.mkdtemp(prefix="arcflow-tactical-")
    db = ArcFlow(data_dir)

    # Seq 1: record the decision.
    db.execute("""
        CREATE (d:Decision {
            id: 'd-001',
            entity_key: 'alpha-03',
            assigned_role: 'primary',
            confidence: 0.91
        })
    """)
    print("seq 1: decision recorded (role=primary, conf=0.91)")

    # Seqs 2, 3: overturn — comma-SET produces ONE WAL entry per assignment.
    db.execute("""
        MATCH (d:Decision {id: 'd-001'})
        SET d.assigned_role = 'secondary',
            d.confidence = 0.55
    """)
    print("seq 2: role flipped → secondary")
    print("seq 3: confidence revised → 0.55")

    fields = "d.id AS id, d.assigned_role AS role, d.confidence AS conf"

    # Walk the WAL.
    for seq, label in [
        (1, "decision time"),
        (2, "after role flip, before confidence revision"),
        (3, "fully overturned"),
    ]:
        print(f"\nAS OF seq {seq} ({label}):")
        for r in db.execute(
            f"MATCH (d:Decision) AS OF seq $s RETURN {fields}",
            params={"s": seq},
        ):
            print(f"  {dict(r)}")

    print("\nstate NOW (live read):")
    for r in db.execute(f"MATCH (d:Decision) RETURN {fields}"):
        print(f"  {dict(r)}")

    print("\nObservations:")
    print("  - The WAL captures every execute() mutation deterministically.")
    print("  - AS OF replay walks the WAL one seq at a time — bit-for-bit reproducible.")
    print("  - Comma-separated SET produces one WAL entry per property assignment.")
    print("  - Decisions you want auditable should go through execute().")
    print("  - Auditors get reproducible queries by including the seq in their reports.")

    db.close()
    shutil.rmtree(data_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
