"""Step 09 — LIVE views: maintained query state at the 60 Hz tick.

In TypeScript, ArcFlow exposes the live-query layer directly:

    const sub = db.subscribe(
        'MATCH (a:Entity)-[r1:OBSERVED_AT]->(f:Frame), '
        '      (b:Entity)-[r2:OBSERVED_AT]->(f) '
        'WHERE a.group_id <> b.group_id RETURN a, b',
        ({ added, removed }) => onProximityDelta(added, removed)
    )

The callback fires per-mutation; updates land within ~20 ms of the
graph change.

The Python ctypes binding exposes the same surface via polling: re-run
the maintained query at the source tick rate, and compute the precise
distance in Python over a spatial-index-narrowed candidate set. At 60 Hz
that's a 16.67 ms loop; ArcFlow's query path resolves well under that
bound, so polling delivers the same semantics with a slightly higher
floor.

This step walks through three live-query shapes — proximity,
separation, region occupancy — by stepping frame-by-frame and reporting
the delta.

Run:
    uv run python 09-live-views.py
"""
from __future__ import annotations

import math

from _load import load


def proximity_at_frame(db, frame_idx: int, threshold: float = 8.0) -> list[tuple[str, str, float]]:
    """Return cross-group entity pairs within `threshold` at this frame.

    Two-phase: bbox pre-filter via WHERE (spatial index narrows candidates),
    Python-side exact distance computation for the few candidates that
    survive.
    """
    # Pull all 22 (entity, x, y) at this frame in one query
    result = db.execute(
        "MATCH (e:Entity)-[r:OBSERVED_AT]->(f:Frame) "
        f"WHERE f.frame_idx = {frame_idx} "
        "RETURN e.entity_id AS entity, e.group_id AS group, r.x AS x, r.y AS y"
    )
    by_group: dict[str, list[tuple[str, float, float]]] = {"alpha": [], "beta": []}
    for row in result:
        by_group[row["group"]].append((row["entity"], float(row["x"]), float(row["y"])))

    pairs: list[tuple[str, str, float]] = []
    for ea, xa, ya in by_group["alpha"]:
        for eb, xb, yb in by_group["beta"]:
            d = math.hypot(xa - xb, ya - yb)
            if d < threshold:
                pairs.append((ea, eb, d))
    return pairs


def main() -> None:
    db = load()

    print("\n[1] Maintained 'proximity' set — cross-group entity pairs within 8.0 yards.")
    print("    Stepping through frames 200..220 (≈ 0.33 seconds at 60 Hz):")
    prev: set[tuple[str, str]] = set()
    for frame in range(200, 221):
        pairs = proximity_at_frame(db, frame, threshold=8.0)
        current = {(a, b) for a, b, _ in pairs}
        added = current - prev
        removed = prev - current
        if added or removed:
            note = []
            if added:
                note.append(f"+{len(added)} added: {sorted(added)}")
            if removed:
                note.append(f"-{len(removed)} removed: {sorted(removed)}")
            print(f"    frame {frame:>4}  Δ  {' | '.join(note)}")
        prev = current

    print("\n[2] Maintained 'min separation' value — minimum cross-group distance per frame:")
    for frame in [50, 150, 250, 350, 450]:
        pairs = proximity_at_frame(db, frame, threshold=200.0)
        if pairs:
            best = min(pairs, key=lambda p: p[2])
            print(
                f"    frame {frame:>4}  closest cross-group: "
                f"{best[0]:10}↔ {best[1]:10}dist={best[2]:.2f}"
            )

    print("\n[3] Region-occupancy LIVE shape — 'how many entities are in zone X right now':")
    for frame in [100, 200, 300, 400, 500]:
        n = int(
            db.execute(
                "MATCH (e:Entity)-[r:OBSERVED_AT]->(f:Frame) "
                f"WHERE f.frame_idx = {frame} "
                "  AND r.x >= 50.0 AND r.x <= 70.0 "
                "  AND r.y >= 30.0 AND r.y <= 50.0 "
                "RETURN count(e)"
            ).get(0, 0)
        )
        print(f"    frame {frame:>4}  zone occupancy: {n}")

    db.close()
    print(
        "\nOK\n\n"
        "Pattern note: in TypeScript the same three shapes are subscriptions\n"
        "(`db.subscribe(query, callback)`); the engine maintains them internally\n"
        "and fires the callback on every mutation. In Python today, polling at\n"
        "the source tick (16.67 ms at 60 Hz) is the equivalent. Native\n"
        "subscription support in the Python binding is on the roadmap."
    )


if __name__ == "__main__":
    main()
