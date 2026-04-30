"""Step 02 — Load data/corpus.json into ArcFlow.

Run:
    uv run python 02-load.py
"""
from __future__ import annotations

import time

from _load import load


def main() -> None:
    t0 = time.perf_counter()
    db, payload = load(verbose=True)
    elapsed = time.perf_counter() - t0
    n_items = (
        len(payload["documents"])
        + len(payload["entities"])
        + len(payload["mentions"])
        + len(payload["relations"])
    )
    print(f"loaded in {elapsed:.2f}s ({n_items / elapsed:.0f} items/sec)")

    n_docs = db.execute("MATCH (d:Document) RETURN count(d)").get(0, 0)
    n_entities = db.execute("MATCH (e:Entity) RETURN count(e)").get(0, 0)
    n_mentions = db.execute("MATCH (m:Mention) RETURN count(m)").get(0, 0)
    n_relations = db.execute("MATCH (r:Relation) RETURN count(r)").get(0, 0)
    n_has = db.execute("MATCH ()-[r:HAS]->() RETURN count(r)").get(0, 0)
    n_cites = db.execute("MATCH ()-[r:CITES]->() RETURN count(r)").get(0, 0)

    print(
        f"in-graph: documents={n_docs}, entities={n_entities}, "
        f"mentions={n_mentions}, relations={n_relations}"
    )
    print(f"          HAS edges={n_has}, CITES edges={n_cites}")
    db.close()
    print("OK")


if __name__ == "__main__":
    main()
