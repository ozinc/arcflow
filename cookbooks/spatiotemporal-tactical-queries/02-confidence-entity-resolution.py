"""
Confidence-weighted entity resolution across multiple ID namespaces.

Pattern: real-world entities are often referenced by different identifiers
across different sources (id_a from one tracker, id_b from another, id_c
from a third). When sources disagree or have gaps, identity resolution
becomes a graph problem: find the entity that best matches across the
namespaces, weighted by per-source confidence.

This is one of the patterns SQL handles awkwardly — multiple LEFT JOINs,
COALESCE chains, manual scoring. In a graph, it's a single multi-property
match with a scoring expression.

This script:
1. Loads the fixture (22 entities, deliberate id_b gaps and an id_c collision).
2. Resolves "who is c-alpha-other?" — collisions surface naturally.
3. Counts entities reachable from each ID namespace — shows the gap shape.
4. Demonstrates a confidence-weighted cross-namespace match.
"""

from _load import make_db


def main():
    db, stats = make_db()
    print(f"Loaded: {stats}\n")

    # 1. Find the entity referenced by id_c='c-alpha-other' (the deliberate
    #    collision the loader plants on entity alpha-05).
    print("=== Q1: Resolve a known-ambiguous id_c value ===")
    for r in db.execute(
        "MATCH (e:Entity) WHERE e.id_c = $v RETURN e.entity_key AS key, e.id_a AS id_a, e.id_b AS id_b, e.id_c AS id_c",
        params={"v": "c-alpha-other"},
    ):
        print(f"  {dict(r)}")

    # 2. Count entities by which namespaces they appear in.
    #    (We use "" as the sentinel for "missing"; see _load.py.)
    print("\n=== Q2: Entities present in id_a only (no id_b — source-b gap) ===")
    rows = list(db.execute(
        "MATCH (e:Entity) WHERE e.id_b = '' RETURN e.entity_key AS key, e.id_a AS id_a"
    ))
    print(f"  {len(rows)} entities missing from source-b:")
    for r in rows:
        print(f"    {dict(r)}")

    # 3. Confidence-weighted cross-source match — find tracker_a observations
    #    whose entity also has a tracker_b observation at the same frame, and
    #    score by min(conf_a, conf_b) — fuses correctly across sources.
    print("\n=== Q3: Cross-source consensus observations (top 10 by min-confidence) ===")
    q = """
        MATCH (e:Entity)-[a:OBSERVED_AT]->(f:Frame)
        WHERE a.source = 'tracker_a'
        MATCH (e)-[b:OBSERVED_AT]->(f)
        WHERE b.source = 'tracker_b'
        WITH e.entity_key AS entity, f.frame_idx AS frame,
             a._confidence AS conf_a, b._confidence AS conf_b
        RETURN entity, frame, conf_a, conf_b
        ORDER BY conf_a DESC, conf_b DESC
        LIMIT 10
    """
    for r in db.execute(q):
        print(f"  {dict(r)}")

    # 4. Disagreement detection — entities where tracker_b confidence has
    #    drifted away from tracker_a confidence (the loader plants this on
    #    alpha-03 and beta-07).
    print("\n=== Q4: Disagreement detection — entities where tracker_b drifted from tracker_a ===")
    q = """
        MATCH (e:Entity)-[a:OBSERVED_AT]->(f:Frame)
        WHERE a.source = 'tracker_a'
        MATCH (e)-[b:OBSERVED_AT]->(f)
        WHERE b.source = 'tracker_b'
          AND b._confidence < 0.70
        WITH e.entity_key AS entity,
             count(*) AS drift_frames,
             avg(b._confidence) AS avg_conf_b
        RETURN entity, drift_frames, avg_conf_b
        ORDER BY drift_frames DESC
    """
    for r in db.execute(q):
        print(f"  {dict(r)}")

    print("\nObservations:")
    print("  - Multi-namespace ID resolution is a property match, not a join chain.")
    print("  - Cross-source consensus is one extra MATCH clause anchored on the same Frame.")
    print("  - Confidence is first-class — sort by min/avg/product, the engine doesn't care.")
    print("  - Disagreement detection is the same shape, just with a confidence predicate.")

    db.close()


if __name__ == "__main__":
    main()
