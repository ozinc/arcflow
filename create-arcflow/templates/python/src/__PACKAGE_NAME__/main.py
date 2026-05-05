"""Entry point — exercises ArcFlow's fast Python paths.

Demonstrates:
  1. bulk_create_nodes / bulk_create_relationships — ~1M ops/sec ingest
  2. Parameterised execute()                       — typed params, no escape bugs
  3. result.to_polars() / .to_arrow()              — zero-copy results

Run:
  python -m {{PACKAGE_NAME}}.main
"""

from __future__ import annotations

from arcflow import ArcFlow


def main() -> None:
    with ArcFlow() as db:
        # Bulk ingest — bypass the parser. Returns NodeIds in input order.
        person_ids = db.bulk_create_nodes(
            [
                (["Person"], {"name": "Alice", "age": 30}),
                (["Person"], {"name": "Bob",   "age": 25}),
                (["Person"], {"name": "Carol", "age": 35}),
            ]
        )

        # Bulk-create edges, addressing nodes by the IDs we just got back.
        db.bulk_create_relationships(
            "KNOWS",
            [
                (person_ids[0], person_ids[1], {"since": 2020}),
                (person_ids[1], person_ids[2], {"since": 2021}),
                (person_ids[0], person_ids[2], {"since": 2019}),
            ],
        )

        # Parameterised query — typed params (no string-escaping bugs).
        adults = db.execute(
            "MATCH (p:Person) WHERE p.age >= $min RETURN p.name, p.age ORDER BY p.age",
            {"min": 30},
        )

        # Zero-copy results into Polars (Arrow C Data Interface under the hood).
        print(adults.to_polars())

        # Graph algorithm — no projection, no catalog setup.
        ranks = db.execute("CALL algo.pageRank()")
        print(f"\nPageRank: {len(ranks)} ranked nodes")
        for row in ranks:
            print(f"  {row['name']}: {row['rank']}")


if __name__ == "__main__":
    main()
