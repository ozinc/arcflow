"""Smoke tests covering the four fast-path surfaces."""

from __future__ import annotations

from arcflow import ArcFlow


def test_bulk_create_and_query() -> None:
    with ArcFlow() as db:
        ids = db.bulk_create_nodes(
            [
                (["Person"], {"name": "Alice"}),
                (["Person"], {"name": "Bob"}),
            ]
        )
        assert len(ids) == 2

        result = db.execute("MATCH (n:Person) RETURN n.name ORDER BY n.name")
        names = [row["n.name"] for row in result]
        assert names == ["Alice", "Bob"]


def test_parameterised_execute() -> None:
    with ArcFlow() as db:
        db.bulk_create_nodes([(["Person"], {"name": "Alice", "age": 30})])
        result = db.execute(
            "MATCH (p:Person {name: $name}) RETURN p.age", {"name": "Alice"}
        )
        assert int(result.get(0, 0)) == 30


def test_bulk_create_relationships_and_algorithm() -> None:
    with ArcFlow() as db:
        ids = db.bulk_create_nodes([(["Node"], {"id": i}) for i in range(3)])
        db.bulk_create_relationships(
            "LINK",
            [
                (ids[0], ids[1], {}),
                (ids[1], ids[2], {}),
                (ids[2], ids[0], {}),
            ],
        )
        ranks = db.execute("CALL algo.pageRank()")
        assert ranks.row_count >= 3


def test_arrow_zero_copy() -> None:
    with ArcFlow() as db:
        db.bulk_create_nodes([(["X"], {"i": i, "name": f"x{i}"}) for i in range(10)])
        tbl = db.execute("MATCH (n:X) RETURN n.i, n.name ORDER BY n.i").to_arrow()
        assert tbl.num_rows == 10
        assert tbl.column_names == ["n.i", "n.name"]
